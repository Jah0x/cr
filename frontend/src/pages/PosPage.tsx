import { useCallback, useEffect, useMemo, useState } from 'react'
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
  created_at: string
  items: SaleItem[]
  payments: PaymentRecord[]
  send_to_terminal: boolean
}

interface SaleSummary {
  id: string
  status: string
  total_amount: number
  currency: string
  created_at: string
  created_by_user_id: string | null
  send_to_terminal: boolean
  payments: PaymentRecord[]
}

interface CashierUser {
  id: string
  email: string
  roles: Array<{ id: string; name: string }>
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
  const [showPaymentExtras, setShowPaymentExtras] = useState(false)
  const [sale, setSale] = useState<SaleDetail | null>(null)
  const [error, setError] = useState('')
  const [sendToTerminal, setSendToTerminal] = useState(false)
  const [salesHistory, setSalesHistory] = useState<SaleSummary[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const [cashiers, setCashiers] = useState<CashierUser[]>([])
  const [cashierFilter, setCashierFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [paymentMethodFilter, setPaymentMethodFilter] = useState('')
  const historyPageSize = 20
  const [historyVisibleCount, setHistoryVisibleCount] = useState(historyPageSize)
  const [historyServerLimit, setHistoryServerLimit] = useState(historyPageSize)
  const [historySupportsLimit, setHistorySupportsLimit] = useState(true)
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [selectedSale, setSelectedSale] = useState<SaleDetail | null>(null)
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

  useEffect(() => {
    const loadCashiers = async () => {
      try {
        const res = await api.get('/users')
        setCashiers(res.data as CashierUser[])
      } catch {
        setCashiers([])
      }
    }
    loadCashiers()
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

  const formatDateTime = (value: string) => {
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return value
    return new Intl.DateTimeFormat(i18n.language || undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(parsed)
  }

  const normalizeSaleStatus = (status: string) => {
    switch (status) {
      case 'draft':
        return t('pos.statusDraft')
      case 'completed':
        return t('pos.statusCompleted')
      case 'cancelled':
        return t('pos.statusCancelled')
      default:
        return status
    }
  }

  const paymentSummary = (salePayments: PaymentRecord[]) => {
    if (!salePayments || salePayments.length === 0) return '—'
    const methods = Array.from(
      new Set(
        salePayments.map((payment) => {
          const normalized = normalizePaymentMethod(String(payment.method))
          return paymentLabels[normalized] ?? String(payment.method)
        })
      )
    )
    return methods.join(', ')
  }

  const cashierLabel = (cashierId: string | null) => {
    if (!cashierId) return '—'
    const cashier = cashiers.find((user) => user.id === cashierId)
    return cashier ? cashier.email : cashierId
  }

  const productNameById = useMemo(() => {
    return new Map(products.map((product) => [product.id, product.name]))
  }, [products])

  const getSaleSubtotal = (saleDetail: SaleDetail) =>
    saleDetail.items.reduce((sum, item) => sum + Number(item.line_total ?? item.qty * item.unit_price), 0)

  const getSaleTaxSummary = useCallback(
    (saleDetail: SaleDetail) => {
      const subtotalValue = getSaleSubtotal(saleDetail)
      if (!taxSettings.enabled || activeTaxRules.length === 0) {
        return { totalTax: 0, lines: [] as Array<{ rule: TaxRule; amount: number }> }
      }
      const totalsByMethod = saleDetail.payments.reduce<Record<PaymentMethod, number>>(
        (acc, payment) => {
          const normalized = normalizePaymentMethod(String(payment.method))
          acc[normalized] += Number(payment.amount)
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
      const ruleTotals = new Map<string, number>()
      methodShares.forEach(({ method, share }) => {
        const grossMethod = subtotalValue * share
        const applicableRules =
          method === null ? activeTaxRules : activeTaxRules.filter((rule) => rule.applies_to.includes(method))
        if (applicableRules.length === 0) return
        if (taxSettings.mode === 'inclusive') {
          const totalRate = applicableRules.reduce((rateSum, rule) => rateSum + (Number(rule.rate) || 0), 0)
          if (totalRate <= 0) return
          const taxTotal = grossMethod - grossMethod / (1 + totalRate / 100)
          applicableRules.forEach((rule) => {
            const portion = taxTotal * ((Number(rule.rate) || 0) / totalRate)
            ruleTotals.set(rule.id, (ruleTotals.get(rule.id) ?? 0) + portion)
          })
        } else {
          applicableRules.forEach((rule) => {
            const portion = grossMethod * ((Number(rule.rate) || 0) / 100)
            ruleTotals.set(rule.id, (ruleTotals.get(rule.id) ?? 0) + portion)
          })
        }
      })
      const lines = activeTaxRules.map((rule) => ({
        rule,
        amount: applyRounding(ruleTotals.get(rule.id) ?? 0)
      }))
      const totalTax = applyRounding(lines.reduce((sum, line) => sum + line.amount, 0))
      return { totalTax, lines }
    },
    [activeTaxRules, applyRounding, taxSettings.enabled, taxSettings.mode]
  )

  const saleTaxSummary = useMemo(() => {
    if (!selectedSale) return null
    return getSaleTaxSummary(selectedSale)
  }, [getSaleTaxSummary, selectedSale])

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

  const adjustQty = (productId: string, delta: number) => {
    setCartItems((prev) =>
      prev
        .map((item) => {
          if (item.product.id !== productId) return item
          const nextQty = item.qty + delta
          return nextQty > 0 ? { ...item, qty: nextQty } : item
        })
        .filter((item) => item.qty > 0)
    )
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

  const hasDraft = cartItems.length > 0 || payments.length > 0
  const canFinalize = cartItems.length > 0

  const clearDraft = useCallback(() => {
    setCartItems([])
    setPayments([])
    setSale(null)
    setError('')
    setPaymentAmount('0')
    setPaymentReference('')
    setSendToTerminal(false)
  }, [])

  const finalizeSale = useCallback(async () => {
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
  }, [cartItems, currencyCode, payments, sendToTerminal, t])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.repeat) return
      const target = event.target as HTMLElement | null
      const isEditable =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement
      if (event.key === 'Escape') {
        if (!hasDraft) return
        const confirmClear = window.confirm('Очистить черновик продажи?')
        if (!confirmClear) return
        event.preventDefault()
        clearDraft()
      }
      if (event.key === 'Enter') {
        if (isEditable) return
        if (!canFinalize) return
        event.preventDefault()
        void finalizeSale()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [canFinalize, clearDraft, finalizeSale, hasDraft])

  const toIsoDate = (value: string, endOfDay = false) => {
    if (!value) return undefined
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return undefined
    if (endOfDay) {
      parsed.setHours(23, 59, 59, 999)
    } else {
      parsed.setHours(0, 0, 0, 0)
    }
    return parsed.toISOString()
  }

  const loadSalesHistory = async (nextLimit = historyPageSize) => {
    setHistoryLoading(true)
    setHistoryError('')
    const params: Record<string, string> = {}
    if (cashierFilter) params.cashier_id = cashierFilter
    const isoFrom = toIsoDate(dateFrom)
    if (isoFrom) params.date_from = isoFrom
    const isoTo = toIsoDate(dateTo, true)
    if (isoTo) params.date_to = isoTo
    if (paymentMethodFilter) params.payment_method = paymentMethodFilter
    params.limit = String(nextLimit)
    try {
      const res = await api.get('/sales', { params })
      const data = res.data as SaleSummary[]
      setSalesHistory(data)
      setHistoryServerLimit(nextLimit)
      setHistorySupportsLimit(data.length <= nextLimit)
      if (nextLimit === historyPageSize) {
        setHistoryVisibleCount(historyPageSize)
      } else {
        setHistoryVisibleCount(Math.min(nextLimit, data.length))
      }
    } catch (e) {
      setHistoryError(getApiErrorMessage(e, t, 'common.error'))
    } finally {
      setHistoryLoading(false)
    }
  }

  const resetHistoryFilters = () => {
    setCashierFilter('')
    setDateFrom('')
    setDateTo('')
    setPaymentMethodFilter('')
  }

  const handleLoadMoreHistory = () => {
    if (historySupportsLimit && salesHistory.length >= historyServerLimit) {
      void loadSalesHistory(historyServerLimit + historyPageSize)
      return
    }
    setHistoryVisibleCount((prev) => Math.min(prev + historyPageSize, salesHistory.length))
  }

  const openSaleDetail = async (saleId: string) => {
    setDetailModalOpen(true)
    setDetailLoading(true)
    setDetailError('')
    setSelectedSale(null)
    try {
      const res = await api.get(`/sales/${saleId}`)
      setSelectedSale(res.data as SaleDetail)
    } catch (e) {
      setDetailError(getApiErrorMessage(e, t, 'common.error'))
    } finally {
      setDetailLoading(false)
    }
  }

  const closeSaleDetail = () => {
    setDetailModalOpen(false)
    setDetailError('')
    setSelectedSale(null)
  }

  const visibleSalesHistory = useMemo(
    () => salesHistory.slice(0, historyVisibleCount),
    [historyVisibleCount, salesHistory]
  )
  const historyHasMore = historySupportsLimit
    ? salesHistory.length >= historyServerLimit
    : historyVisibleCount < salesHistory.length

  useEffect(() => {
    loadSalesHistory()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
        <div className="pos-cart-column">
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
                      <div className="pos-qty-controls">
                        <button
                          type="button"
                          className="pos-qty-button"
                          onClick={() => adjustQty(item.product.id, -1)}
                          aria-label="Уменьшить количество"
                        >
                          -
                        </button>
                        <span>{item.qty}</span>
                        <button
                          type="button"
                          className="pos-qty-button"
                          onClick={() => adjustQty(item.product.id, 1)}
                          aria-label="Увеличить количество"
                        >
                          +
                        </button>
                      </div>
                      <span>{formatCurrency(item.qty * item.product.price)}</span>
                      <button
                        className="pos-cart-remove"
                        onClick={() => removeItem(item.product.id)}
                        aria-label={t('pos.remove')}
                      >
                        ✕
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
              <div className="pos-payment-methods">
                {paymentMethods.map((method) => (
                  <button
                    key={method}
                    type="button"
                    className={`pos-payment-method ${paymentMethod === method ? 'is-selected' : ''}`}
                    onClick={() => setPaymentMethod(method)}
                    aria-pressed={paymentMethod === method}
                  >
                    {paymentLabels[method]}
                  </button>
                ))}
              </div>
              <input
                placeholder={t('pos.amount')}
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
              />
              <button onClick={addPayment}>{t('pos.addPayment')}</button>
            </div>
            <div className="pos-payment-extras">
              <button
                type="button"
                className="secondary"
                onClick={() => setShowPaymentExtras((prev) => !prev)}
                aria-expanded={showPaymentExtras}
              >
                Дополнительно
              </button>
              {showPaymentExtras && (
                <input
                  placeholder={t('pos.reference')}
                  value={paymentReference}
                  onChange={(e) => setPaymentReference(e.target.value)}
                />
              )}
            </div>
            <div className="pos-payment-options">
              <label className="form-inline pos-payment-options__label">
                <input
                  type="checkbox"
                  checked={sendToTerminal}
                  onChange={(e) => setSendToTerminal(e.target.checked)}
                />
                <span>Отправлять в терминал (позже)</span>
              </label>
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
            <button className="pos-finalize" onClick={finalizeSale} disabled={!canFinalize}>
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
      <section className="card pos-history">
        <div className="pos-history-header">
          <div>
            <h3>{t('pos.historyTitle')}</h3>
            <p className="page-subtitle">{t('pos.historySubtitle')}</p>
          </div>
          <div className="pos-history-actions">
            <button className="secondary" onClick={resetHistoryFilters}>
              {t('pos.historyReset')}
            </button>
            <button onClick={loadSalesHistory}>{t('pos.historyApply')}</button>
          </div>
        </div>
        <div className="pos-history-filters">
          <label>
            <span>{t('pos.historyCashier')}</span>
            <select value={cashierFilter} onChange={(e) => setCashierFilter(e.target.value)}>
              <option value="">{t('pos.historyAllCashiers')}</option>
              {cashiers
                .filter((user) => user.roles.some((role) => role.name === 'cashier' || role.name === 'owner'))
                .map((cashier) => (
                  <option key={cashier.id} value={cashier.id}>
                    {cashier.email}
                  </option>
                ))}
            </select>
          </label>
          <label>
            <span>{t('pos.historyDateFrom')}</span>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label>
            <span>{t('pos.historyDateTo')}</span>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
          <label>
            <span>{t('pos.historyPaymentMethod')}</span>
            <select value={paymentMethodFilter} onChange={(e) => setPaymentMethodFilter(e.target.value)}>
              <option value="">{t('pos.historyAllPayments')}</option>
              <option value="cash">{t('pos.paymentMethodCash')}</option>
              <option value="card">{t('pos.paymentMethodCard')}</option>
              <option value="transfer">{t('pos.paymentMethodTransfer')}</option>
            </select>
          </label>
        </div>
        {historyLoading ? (
          <p className="page-subtitle">{t('common.loading')}</p>
        ) : historyError ? (
          <p className="pos-error">{historyError}</p>
        ) : salesHistory.length === 0 ? (
          <p className="page-subtitle">{t('pos.historyEmpty')}</p>
        ) : (
          <div className="pos-history-table-wrapper">
            <table className="pos-history-table">
              <thead>
                <tr>
                  <th>{t('common.created')}</th>
                  <th>{t('pos.sale')}</th>
                  <th>{t('pos.historyCashier')}</th>
                  <th>{t('pos.historyPaymentMethod')}</th>
                  <th>{t('pos.status')}</th>
                  <th>{t('pos.sendToTerminal')}</th>
                  <th>{t('pos.total')}</th>
                </tr>
              </thead>
              <tbody>
                {visibleSalesHistory.map((entry) => (
                  <tr
                    key={entry.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => openSaleDetail(entry.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        void openSaleDetail(entry.id)
                      }
                    }}
                  >
                    <td>{formatDateTime(entry.created_at)}</td>
                    <td>{entry.id}</td>
                    <td>{cashierLabel(entry.created_by_user_id)}</td>
                    <td>{paymentSummary(entry.payments)}</td>
                    <td>{normalizeSaleStatus(entry.status)}</td>
                    <td>{entry.send_to_terminal ? t('common.yes') : t('common.no')}</td>
                    <td>{formatCurrency(Number(entry.total_amount))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!historyLoading && !historyError && salesHistory.length > 0 && historyHasMore && (
          <div className="pos-history-actions">
            <button className="secondary" onClick={handleLoadMoreHistory}>
              {t('pos.loadMore')}
            </button>
          </div>
        )}
      </section>
      {detailModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('pos.saleDetails')}</h4>
              <button className="ghost" onClick={closeSaleDetail}>
                {t('common.cancel')}
              </button>
            </div>
            <div className="form-stack">
              {detailLoading ? (
                <p className="page-subtitle">{t('common.loading')}</p>
              ) : detailError ? (
                <p className="pos-error">{detailError}</p>
              ) : selectedSale ? (
                <>
                  <div className="form-stack">
                    <div>
                      <strong>{t('pos.sale')}</strong> {selectedSale.id}
                    </div>
                    <div>
                      <strong>{t('common.created')}</strong> {formatDateTime(selectedSale.created_at)}
                    </div>
                    <div>
                      <strong>{t('pos.status')}</strong> {normalizeSaleStatus(selectedSale.status)}
                    </div>
                  </div>
                  <div className="table-wrapper">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>{t('pos.product')}</th>
                          <th>{t('pos.qty')}</th>
                          <th>{t('pos.price')}</th>
                          <th>{t('pos.total')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedSale.items.map((item) => (
                          <tr key={item.id}>
                            <td>{productNameById.get(item.product_id) ?? item.product_id}</td>
                            <td>{item.qty}</td>
                            <td>{formatCurrency(Number(item.unit_price))}</td>
                            <td>{formatCurrency(Number(item.line_total))}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="form-stack">
                    <h5>{t('pos.taxes')}</h5>
                    {taxSettings.enabled && activeTaxRules.length > 0 && saleTaxSummary ? (
                      <>
                        {saleTaxSummary.lines.map((line) => (
                          <div key={line.rule.id} className="pos-summary-row">
                            <span>
                              {line.rule.name} ({Number(line.rule.rate).toFixed(2)}%)
                            </span>
                            <strong>{formatCurrency(line.amount)}</strong>
                          </div>
                        ))}
                        <div className="pos-summary-row total">
                          <span>{t('pos.total')}</span>
                          <strong>{formatCurrency(saleTaxSummary.totalTax)}</strong>
                        </div>
                      </>
                    ) : (
                      <p className="page-subtitle">—</p>
                    )}
                  </div>
                </>
              ) : (
                <p className="page-subtitle">—</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
