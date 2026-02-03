import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useTenantSettings } from '../api/tenantSettings'

type PaymentMethod = 'cash' | 'card' | 'transfer'

interface Product {
  id: string
  name: string
  price: number
  image_url?: string | null
}

interface CartItem {
  product: Product
  qty: number
}

interface PaymentDraft {
  amount: number
  method: PaymentMethod
  reference: string
}

interface SaleItem {
  id: string
  product_id: string
  qty: number
  unit_price: number
  line_total: number
}

interface PaymentRecord {
  id: string
  amount: number
  method: PaymentMethod
  status: string
  reference: string
}

interface SaleDetail {
  id: string
  status: string
  total_amount: number
  currency: string
  items: SaleItem[]
  payments: PaymentRecord[]
  send_to_terminal: boolean
}

type TaxRule = {
  id: string
  name: string
  rate: number
  is_active: boolean
  applies_to: PaymentMethod[]
}

type TaxSettings = {
  enabled: boolean
  mode: 'exclusive' | 'inclusive'
  rounding: 'round' | 'ceil' | 'floor'
  rules: TaxRule[]
}

const defaultTaxSettings: TaxSettings = {
  enabled: false,
  mode: 'exclusive',
  rounding: 'round',
  rules: []
}

const paymentMethods: PaymentMethod[] = ['cash', 'card', 'transfer']

const normalizePaymentMethod = (method: string): PaymentMethod => {
  if (method === 'external') return 'transfer'
  return method as PaymentMethod
}

export default function PosPage() {
  const { t, i18n } = useTranslation()
  const [products, setProducts] = useState<Product[]>([])
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [payments, setPayments] = useState<PaymentDraft[]>([])
  const [search, setSearch] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('0')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash')
  const [paymentReference, setPaymentReference] = useState('')
  const [sale, setSale] = useState<SaleDetail | null>(null)
  const [error, setError] = useState('')
  const [sendToTerminal, setSendToTerminal] = useState(false)
  const { data: tenantSettings } = useTenantSettings()
  const paymentLabels: Record<PaymentMethod, string> = {
    cash: t('pos.paymentMethodCash'),
    card: t('pos.paymentMethodCard'),
    transfer: t('pos.paymentMethodTransfer')
  }

  useEffect(() => {
    api.get('/products').then((res) => {
      const normalized = (res.data as Array<{ id: string; name: string; sell_price: number; image_url?: string | null }>)
        .map((product) => ({
          id: product.id,
          name: product.name,
          price: Number(product.sell_price ?? 0),
          image_url: product.image_url ?? null
        }))
      setProducts(normalized)
    })
  }, [])

  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return products
    return products.filter((product) => product.name.toLowerCase().includes(query))
  }, [products, search])

  const subtotal = useMemo(() => {
    return cartItems.reduce((sum, item) => sum + item.qty * item.product.price, 0)
  }, [cartItems])

  const paidTotal = useMemo(() => {
    return payments.reduce((sum, payment) => sum + payment.amount, 0)
  }, [payments])

  const taxSettings = useMemo<TaxSettings>(() => {
    const stored = tenantSettings?.settings?.taxes
    if (!stored || typeof stored !== 'object') return defaultTaxSettings
    const rules = Array.isArray((stored as TaxSettings).rules) ? (stored as TaxSettings).rules : []
    return {
      ...defaultTaxSettings,
      ...(stored as Partial<TaxSettings>),
      rules: rules.map((rule) => ({
        ...rule,
        applies_to:
          Array.isArray(rule.applies_to) && rule.applies_to.length > 0
            ? rule.applies_to.map((method) => normalizePaymentMethod(method))
            : paymentMethods
      }))
    }
  }, [tenantSettings?.settings])

  const activeTaxRules = useMemo(
    () => taxSettings.rules.filter((rule) => rule.is_active),
    [taxSettings.rules]
  )

  const totalTaxRate = useMemo(
    () => activeTaxRules.reduce((sum, rule) => sum + (Number(rule.rate) || 0), 0),
    [activeTaxRules]
  )

  const applyRounding = (value: number) => {
    switch (taxSettings.rounding) {
      case 'ceil':
        return Math.ceil(value * 100) / 100
      case 'floor':
        return Math.floor(value * 100) / 100
      default:
        return Math.round(value * 100) / 100
    }
  }

  const taxAmount = useMemo(() => {
    if (!taxSettings.enabled || activeTaxRules.length === 0) return 0
    const totalsByMethod = payments.reduce<Record<PaymentMethod, number>>(
      (acc, payment) => {
        acc[payment.method] += payment.amount
        return acc
      },
      { cash: 0, card: 0, transfer: 0 }
    )
    const totalPaid = Object.values(totalsByMethod).reduce((sum, value) => sum + value, 0)
    const methodShares =
      totalPaid > 0
        ? paymentMethods.map((method) => ({
            method,
            share: totalsByMethod[method] / totalPaid
          }))
        : [{ method: null, share: 1 }]
    const totalTax = methodShares.reduce((sum, { method, share }) => {
      const grossMethod = subtotal * share
      const applicableRules =
        method === null ? activeTaxRules : activeTaxRules.filter((rule) => rule.applies_to.includes(method))
      if (applicableRules.length === 0) return sum
      if (taxSettings.mode === 'inclusive') {
        const totalRate = applicableRules.reduce((rateSum, rule) => rateSum + (Number(rule.rate) || 0), 0)
        if (totalRate <= 0) return sum
        const taxTotal = grossMethod - grossMethod / (1 + totalRate / 100)
        const allocated = applicableRules.reduce((ruleSum, rule) => {
          return ruleSum + taxTotal * ((Number(rule.rate) || 0) / totalRate)
        }, 0)
        return sum + allocated
      }
      const methodTax = applicableRules.reduce((ruleSum, rule) => {
        return ruleSum + grossMethod * ((Number(rule.rate) || 0) / 100)
      }, 0)
      return sum + methodTax
    }, 0)
    return applyRounding(totalTax)
  }, [activeTaxRules, applyRounding, payments, subtotal, taxSettings.enabled, taxSettings.mode])

  const totalWithTax = taxSettings.enabled && taxSettings.mode === 'exclusive' ? subtotal + taxAmount : subtotal

  const totalDue = Math.max(totalWithTax - paidTotal, 0)
  const taxLabel = taxSettings.mode === 'inclusive' ? t('pos.taxIncluded') : t('pos.taxAdded')

  const currencyCode = useMemo(() => {
    const currency =
      typeof tenantSettings?.settings?.currency === 'string' && tenantSettings?.settings?.currency.trim()
        ? tenantSettings.settings.currency
        : 'RUB'
    return currency
  }, [tenantSettings?.settings])

  const currencyFormatter = useMemo(() => {
    return new Intl.NumberFormat(i18n.language || undefined, {
      style: 'currency',
      currency: currencyCode
    })
  }, [currencyCode, i18n.language])

  const formatCurrency = (value: number) => currencyFormatter.format(value)

  const addToCart = (product: Product) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.product.id === product.id)
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, qty: item.qty + 1 } : item
        )
      }
      return [...prev, { product, qty: 1 }]
    })
  }

  const updateQty = (productId: string, qty: number) => {
    if (Number.isNaN(qty) || qty <= 0) return
    setCartItems((prev) => prev.map((item) => (item.product.id === productId ? { ...item, qty } : item)))
  }

  const removeItem = (productId: string) => {
    setCartItems((prev) => prev.filter((item) => item.product.id !== productId))
  }

  const addPayment = () => {
    const amountValue = Number(paymentAmount)
    if (!amountValue || amountValue <= 0) return
    setPayments((prev) => [...prev, { amount: amountValue, method: paymentMethod, reference: paymentReference }])
    setPaymentAmount('0')
    setPaymentReference('')
  }

  const removePayment = (index: number) => {
    setPayments((prev) => prev.filter((_, idx) => idx !== index))
  }

  const finalizeSale = async () => {
    setError('')
    if (cartItems.length === 0) {
      setError(t('errors.addItemsBeforeFinalize'))
      return
    }
    const itemPayload = {
      items: cartItems.map((item) => ({
        product_id: item.product.id,
        qty: item.qty,
        unit_price: item.product.price
      })),
      currency: currencyCode,
      send_to_terminal: sendToTerminal
    }
    const completePayload = {
      payments: payments.map((payment) => ({
        amount: payment.amount,
        method: payment.method,
        reference: payment.reference
      }))
    }
    let draftId: string | null = null
    try {
      const draftRes = await api.post('/sales/draft', { currency: currencyCode, send_to_terminal: sendToTerminal })
      draftId = draftRes.data.id
      await api.put(`/sales/${draftId}`, itemPayload)
      const completeRes = await api.post(`/sales/${draftId}/complete`, completePayload)
      setSale(completeRes.data)
      setCartItems([])
      setPayments([])
    } catch (e) {
      if (draftId) {
        try {
          await api.post(`/sales/${draftId}/cancel`)
        } catch {
          // ignore draft cleanup errors
        }
      }
      setError(getApiErrorMessage(e, t, 'errors.finalizeSaleFailed'))
    }
  }

  return (
    <div className="page pos-page">
      <div className="page-header">
        <h2 className="page-title">{t('pos.title')}</h2>
        <p className="page-subtitle">{t('pos.subtitle')}</p>
      </div>
      <div className="pos-layout">
        <section className="card pos-products">
          <div className="pos-search">
            <input
              placeholder={t('pos.searchProducts')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="pos-products-grid">
            {filteredProducts.map((product) => (
              <button key={product.id} onClick={() => addToCart(product)} className="pos-product-card">
                <div className="pos-product-image">
                  {product.image_url ? (
                    <img src={product.image_url} alt={product.name} loading="lazy" />
                  ) : (
                    <span>{t('pos.noImage')}</span>
                  )}
                </div>
                <div className="pos-product-info">
                  <div className="pos-product-name">{product.name}</div>
                  <div className="pos-product-price">{formatCurrency(product.price)}</div>
                </div>
              </button>
            ))}
          </div>
        </section>
        <section className="card pos-cart">
          <h3>{t('pos.cart')}</h3>
          {cartItems.length === 0 ? (
            <p className="page-subtitle">{t('pos.emptyCart')}</p>
          ) : (
            <div className="pos-cart-items">
              {cartItems.map((item) => (
                <div key={item.product.id} className="pos-cart-item">
                  <div className="pos-cart-name">{item.product.name}</div>
                  <div className="pos-cart-controls">
                    <input
                      value={item.qty}
                      onChange={(e) => updateQty(item.product.id, Number(e.target.value))}
                    />
                    <span>{formatCurrency(item.qty * item.product.price)}</span>
                    <button className="secondary" onClick={() => removeItem(item.product.id)}>
                      {t('pos.remove')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="pos-summary">
            <div className="pos-summary-row">
              <span>{t('pos.subtotal')}</span>
              <strong>{formatCurrency(subtotal)}</strong>
            </div>
            {taxSettings.enabled && totalTaxRate > 0 && (
              <div className="pos-summary-row">
                <span>
                  {taxLabel} ({totalTaxRate.toFixed(2)}%)
                </span>
                <strong>{formatCurrency(taxAmount)}</strong>
              </div>
            )}
            <div className="pos-summary-row total">
              <span>{t('pos.total')}</span>
              <strong>{formatCurrency(totalWithTax)}</strong>
            </div>
          </div>
          <h4>{t('pos.payments')}</h4>
          <div className="pos-payment-entry">
            <input
              placeholder={t('pos.amount')}
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
            />
            <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}>
              <option value="cash">{t('pos.paymentMethodCash')}</option>
              <option value="card">{t('pos.paymentMethodCard')}</option>
              <option value="transfer">{t('pos.paymentMethodTransfer')}</option>
            </select>
            <input
              placeholder={t('pos.reference')}
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
            />
            <button onClick={addPayment}>{t('pos.addPayment')}</button>
          </div>
          <div className="pos-payments-list">
            {payments.map((payment, index) => (
              <div key={`${payment.method}-${index}`} className="pos-payment-item">
                <div>
                  {paymentLabels[payment.method]} {formatCurrency(payment.amount)}
                  {payment.reference ? ` (${payment.reference})` : ''}
                </div>
                <button className="ghost" onClick={() => removePayment(index)}>
                  {t('pos.remove')}
                </button>
              </div>
            ))}
          </div>
          <div className="pos-summary-row total">
            <span>{t('pos.due')}</span>
            <strong>{formatCurrency(totalDue)}</strong>
          </div>
          <label className="form-inline">
            <input
              type="checkbox"
              checked={sendToTerminal}
              onChange={(e) => setSendToTerminal(e.target.checked)}
            />
            <span>{t('pos.sendToTerminal')}</span>
          </label>
          <button className="pos-finalize" onClick={finalizeSale}>
            {t('pos.finalize')}
          </button>
          {error && <p className="pos-error">{error}</p>}
          {sale && (
            <div className="pos-sale-summary">
              <p>
                {t('pos.sale')} {sale.id}
              </p>
              <p>
                {t('pos.status')}: {sale.status}
              </p>
              <p>
                {t('pos.total')}: {formatCurrency(Number(sale.total_amount))}
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
