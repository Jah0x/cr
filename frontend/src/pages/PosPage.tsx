import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useTenantSettings } from '../api/tenantSettings'

type PaymentMethod = 'cash' | 'card' | 'external'

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
}

type TaxRule = {
  id: string
  name: string
  rate: number
  is_active: boolean
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

export default function PosPage() {
  const { t } = useTranslation()
  const [products, setProducts] = useState<Product[]>([])
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [payments, setPayments] = useState<PaymentDraft[]>([])
  const [search, setSearch] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('0')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash')
  const [paymentReference, setPaymentReference] = useState('')
  const [sale, setSale] = useState<SaleDetail | null>(null)
  const [error, setError] = useState('')
  const { data: tenantSettings } = useTenantSettings()
  const paymentLabels: Record<PaymentMethod, string> = {
    cash: t('pos.paymentMethodCash'),
    card: t('pos.paymentMethodCard'),
    external: t('pos.paymentMethodExternal')
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
    return {
      ...defaultTaxSettings,
      ...(stored as Partial<TaxSettings>),
      rules: Array.isArray((stored as TaxSettings).rules) ? (stored as TaxSettings).rules : []
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
    if (!taxSettings.enabled || totalTaxRate <= 0) return 0
    if (taxSettings.mode === 'inclusive') {
      const divisor = 1 + totalTaxRate / 100
      if (divisor <= 0) return 0
      return applyRounding(subtotal - subtotal / divisor)
    }
    return applyRounding(subtotal * (totalTaxRate / 100))
  }, [applyRounding, subtotal, taxSettings.enabled, taxSettings.mode, totalTaxRate])

  const totalWithTax = taxSettings.enabled && taxSettings.mode === 'exclusive' ? subtotal + taxAmount : subtotal

  const totalDue = Math.max(totalWithTax - paidTotal, 0)
  const taxLabel = taxSettings.mode === 'inclusive' ? t('pos.taxIncluded') : t('pos.taxAdded')

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
    const payload = {
      items: cartItems.map((item) => ({
        product_id: item.product.id,
        qty: item.qty,
        unit_price: item.product.price
      })),
      payments: payments.map((payment) => ({
        amount: payment.amount,
        method: payment.method,
        reference: payment.reference
      }))
    }
    try {
      const res = await api.post('/sales', payload)
      setSale(res.data)
      setCartItems([])
      setPayments([])
    } catch (e) {
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
                  <div className="pos-product-price">${product.price.toFixed(2)}</div>
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
                    <span>${(item.qty * item.product.price).toFixed(2)}</span>
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
              <strong>${subtotal.toFixed(2)}</strong>
            </div>
            {taxSettings.enabled && totalTaxRate > 0 && (
              <div className="pos-summary-row">
                <span>
                  {taxLabel} ({totalTaxRate.toFixed(2)}%)
                </span>
                <strong>${taxAmount.toFixed(2)}</strong>
              </div>
            )}
            <div className="pos-summary-row total">
              <span>{t('pos.total')}</span>
              <strong>${totalWithTax.toFixed(2)}</strong>
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
              <option value="external">{t('pos.paymentMethodExternal')}</option>
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
                  {paymentLabels[payment.method]} ${payment.amount.toFixed(2)}
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
            <strong>${totalDue.toFixed(2)}</strong>
          </div>
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
                {t('pos.total')}: ${sale.total_amount}
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
