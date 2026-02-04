import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'
import Card from '../components/Card'
import { PrimaryButton, SecondaryButton } from '../components/Buttons'
import { Checkbox, Input, Select } from '../components/FormField'
import PageTitle from '../components/PageTitle'

type ExpenseCategory = { id: string; name: string }

type Expense = {
  id: string
  occurred_at: string
  amount: number
  category_id: string | null
  note: string | null
  payment_method: string | null
}

type PnlReport = {
  total_sales: number
  cogs: number
  gross_profit: number
  expenses_total: number
  net_profit: number
}

type FinanceOverviewReport = {
  total_revenue: number
  gross_profit: number
  total_taxes: number
  revenue_by_method: Partial<Record<PaymentMethod, number>>
  taxes_by_method: Partial<Record<PaymentMethod, number>>
}

type TopProductPerformance = {
  product_id: string
  name: string
  qty: number
  revenue: number
  margin: number
}

type InventoryValuationItem = {
  product_id: string
  name: string
  qty_on_hand: number
  unit_cost: number
  total_value: number
}

type InventoryValuationReport = {
  total_value: number
  items: InventoryValuationItem[]
}

type PaymentMethod = 'cash' | 'card' | 'transfer'

type TaxReportItem = {
  rule_id: string
  name: string
  rate: number
  total_tax: number
  by_method: Partial<Record<PaymentMethod, number>>
}

type FinanceFiltersState = {
  dateFrom: string
  dateTo: string
  taxMethods: PaymentMethod[]
}

const paymentMethods: PaymentMethod[] = ['cash', 'card', 'transfer']

const currencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})

const formatCurrency = (value: number | null | undefined) => {
  const amount = typeof value === 'number' ? value : Number(value ?? 0)
  const formatted = currencyFormatter.format(Number.isFinite(amount) ? amount : 0)
  return formatted.replace(/\u00a0/g, ' ')
}

const toDateParam = (value: string, endOfDay = false) => {
  if (!value) return undefined
  const date = new Date(`${value}T00:00:00`)
  if (endOfDay) {
    date.setHours(23, 59, 59, 999)
  }
  return date.toISOString()
}

const decodeTokenPayload = (token: string) => {
  if (!token) return null
  const tokenParts = token.split('.')
  if (tokenParts.length < 2) return null
  try {
    const normalized = tokenParts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
    const decoded = atob(padded)
    return JSON.parse(decoded) as { tenant_id?: string; sub?: string }
  } catch (error) {
    console.warn('Failed to decode auth token payload', error)
    return null
  }
}

const getStoredUser = () => {
  const rawUser = localStorage.getItem('user')
  if (!rawUser) return null
  try {
    return JSON.parse(rawUser) as { id?: string }
  } catch (error) {
    console.warn('Failed to parse stored user', error)
    return null
  }
}

const defaultFilters: FinanceFiltersState = {
  dateFrom: '',
  dateTo: '',
  taxMethods: paymentMethods
}

const isPaymentMethod = (value: unknown): value is PaymentMethod => {
  return typeof value === 'string' && paymentMethods.includes(value as PaymentMethod)
}

const normalizeFiltersState = (value: unknown): FinanceFiltersState | null => {
  if (!value || typeof value !== 'object') return null
  const record = value as Partial<FinanceFiltersState>
  const dateFrom = typeof record.dateFrom === 'string' ? record.dateFrom : defaultFilters.dateFrom
  const dateTo = typeof record.dateTo === 'string' ? record.dateTo : defaultFilters.dateTo
  const taxMethods = Array.isArray(record.taxMethods)
    ? record.taxMethods.filter(isPaymentMethod)
    : defaultFilters.taxMethods
  return { dateFrom, dateTo, taxMethods }
}

const readStoredFilters = (storageKey: string) => {
  const raw = localStorage.getItem(storageKey)
  if (!raw) return null
  try {
    return normalizeFiltersState(JSON.parse(raw))
  } catch (error) {
    console.warn('Failed to parse stored finance filters', error)
    return null
  }
}

export default function FinancePage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const tokenPayload = useMemo(() => decodeTokenPayload(localStorage.getItem('token') ?? ''), [])
  const storedUser = useMemo(() => getStoredUser(), [])
  const userId = storedUser?.id ?? tokenPayload?.sub
  const tenantId = tokenPayload?.tenant_id
  const storageKey = tenantId && userId ? `finance_filters:${tenantId}:${userId}` : null
  const [categories, setCategories] = useState<ExpenseCategory[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [categoryName, setCategoryName] = useState('')
  const [occurredAt, setOccurredAt] = useState('')
  const [amount, setAmount] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [note, setNote] = useState('')
  const [filters, setFilters] = useState<FinanceFiltersState>(defaultFilters)
  const [draftFilters, setDraftFilters] = useState<FinanceFiltersState>(defaultFilters)
  const [pnl, setPnl] = useState<PnlReport | null>(null)
  const [overview, setOverview] = useState<FinanceOverviewReport | null>(null)
  const [taxes, setTaxes] = useState<TaxReportItem[]>([])
  const [topRevenue, setTopRevenue] = useState<TopProductPerformance[]>([])
  const [topMargin, setTopMargin] = useState<TopProductPerformance[]>([])
  const [inventoryValuation, setInventoryValuation] = useState<InventoryValuationReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const params = useMemo(() => {
    return {
      date_from: toDateParam(filters.dateFrom),
      date_to: toDateParam(filters.dateTo, true)
    }
  }, [filters.dateFrom, filters.dateTo])

  const taxParams = useMemo(() => {
    const methods =
      filters.taxMethods.length > 0 && filters.taxMethods.length < paymentMethods.length
        ? filters.taxMethods.join(',')
        : undefined
    return {
      ...params,
      methods
    }
  }, [params, filters.taxMethods])

  useEffect(() => {
    if (!storageKey) return
    const savedFilters = readStoredFilters(storageKey)
    if (savedFilters) {
      setFilters(savedFilters)
      setDraftFilters(savedFilters)
    }
  }, [storageKey])

  useEffect(() => {
    if (!storageKey) return
    const handle = window.setTimeout(() => {
      const payload: FinanceFiltersState = {
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        taxMethods: filters.taxMethods
      }
      localStorage.setItem(storageKey, JSON.stringify(payload))
    }, 400)
    return () => window.clearTimeout(handle)
  }, [filters, storageKey])

  const loadCategories = async () => {
    const res = await api.get('/finance/expense-categories')
    setCategories(res.data)
  }

  const loadExpenses = async () => {
    const res = await api.get('/finance/expenses', { params })
    setExpenses(res.data)
  }

  const loadPnl = async () => {
    const res = await api.get('/reports/pnl', { params })
    setPnl(res.data)
  }

  const loadOverview = async () => {
    const res = await api.get('/reports/finance-overview', { params })
    setOverview(res.data)
  }

  const loadTaxes = async () => {
    const res = await api.get('/reports/taxes', { params: taxParams })
    setTaxes(res.data)
  }

  const loadTopProducts = async () => {
    const [revenueRes, marginRes] = await Promise.all([
      api.get('/reports/top-products-performance', { params: { ...params, sort: 'revenue' } }),
      api.get('/reports/top-products-performance', { params: { ...params, sort: 'margin' } })
    ])
    setTopRevenue(revenueRes.data)
    setTopMargin(marginRes.data)
  }

  const loadInventoryValuation = async () => {
    const res = await api.get('/reports/inventory-valuation')
    setInventoryValuation(res.data)
  }

  const loadData = async () => {
    setIsLoading(true)
    try {
      await Promise.all([
        loadCategories(),
        loadExpenses(),
        loadPnl(),
        loadOverview(),
        loadTaxes(),
        loadTopProducts(),
        loadInventoryValuation()
      ])
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [params.date_from, params.date_to, taxParams.methods])

  const createCategory = async () => {
    if (!categoryName.trim()) return
    try {
      await api.post('/finance/expense-categories', { name: categoryName })
      setCategoryName('')
      addToast(t('common.created'), 'success')
      loadCategories()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const createExpense = async () => {
    if (!occurredAt || !amount) return
    try {
      await api.post('/finance/expenses', {
        occurred_at: toDateParam(occurredAt),
        amount: Number(amount),
        category_id: categoryId || null,
        payment_method: paymentMethod || null,
        note: note || null
      })
      setOccurredAt('')
      setAmount('')
      setCategoryId('')
      setPaymentMethod('')
      setNote('')
      addToast(t('common.created'), 'success')
      loadExpenses()
      loadPnl()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const setQuickRange = (days: number) => {
    const now = new Date()
    const start = new Date(now)
    start.setDate(now.getDate() - days + 1)
    setDraftFilters((prev) => ({
      ...prev,
      dateFrom: start.toISOString().slice(0, 10),
      dateTo: now.toISOString().slice(0, 10)
    }))
  }

  const toggleTaxMethod = (method: PaymentMethod) => {
    setDraftFilters((prev) => {
      if (prev.taxMethods.includes(method)) {
        return { ...prev, taxMethods: prev.taxMethods.filter((value) => value !== method) }
      }
      return { ...prev, taxMethods: [...prev.taxMethods, method] }
    })
  }

  const resetFilters = () => {
    if (storageKey) {
      localStorage.removeItem(storageKey)
    }
    setFilters(defaultFilters)
    setDraftFilters(defaultFilters)
  }

  const applyFilters = () => {
    setFilters(draftFilters)
  }

  const taxTotal = useMemo(() => {
    return taxes.reduce((sum, item) => sum + Number(item.total_tax || 0), 0)
  }, [taxes])

  const topRevenueTotal = useMemo(() => {
    return topRevenue.reduce((sum, item) => sum + Number(item.revenue || 0), 0)
  }, [topRevenue])

  const topMarginTotal = useMemo(() => {
    return topMargin.reduce((sum, item) => sum + Number(item.margin || 0), 0)
  }, [topMargin])

  const renderSkeletonRows = (rows: number, columns: number) =>
    Array.from({ length: rows }).map((_, rowIndex) => (
      <tr key={`skeleton-${rowIndex}`}>
        {Array.from({ length: columns }).map((__, columnIndex) => (
          <td key={`skeleton-${rowIndex}-${columnIndex}`}>
            <span className="skeleton skeleton-text" />
          </td>
        ))}
      </tr>
    ))

  return (
    <div className="page">
      <PageTitle title={t('finance.title')} />
      <Card title={t('finance.filtersTitle')} subtitle={t('finance.filtersSubtitle')} className="filters-panel">
        <div className="filters-panel__row">
          <div className="filters-panel__presets form-inline">
            <PrimaryButton type="button" onClick={() => setQuickRange(1)}>
              {t('finance.today')}
            </PrimaryButton>
            <PrimaryButton type="button" onClick={() => setQuickRange(7)}>
              {t('finance.week')}
            </PrimaryButton>
            <PrimaryButton type="button" onClick={() => setQuickRange(30)}>
              {t('finance.month')}
            </PrimaryButton>
          </div>
          <div className="filters-panel__dates">
            <Input
              label={t('finance.dateFrom')}
              type="date"
              value={draftFilters.dateFrom}
              onChange={(event) => setDraftFilters((prev) => ({ ...prev, dateFrom: event.target.value }))}
            />
            <Input
              label={t('finance.dateTo')}
              type="date"
              value={draftFilters.dateTo}
              onChange={(event) => setDraftFilters((prev) => ({ ...prev, dateTo: event.target.value }))}
            />
          </div>
          <div className="filters-panel__taxes">
            {paymentMethods.map((method) => (
              <Checkbox
                key={method}
                checked={draftFilters.taxMethods.includes(method)}
                onChange={() => toggleTaxMethod(method)}
                label={t(`finance.taxMethod.${method}`)}
              />
            ))}
          </div>
          <div className="filters-panel__actions">
            <PrimaryButton type="button" onClick={applyFilters}>
              {t('finance.applyFilters')}
            </PrimaryButton>
            <SecondaryButton type="button" onClick={resetFilters}>
              {t('finance.resetFilters')}
            </SecondaryButton>
          </div>
        </div>
      </Card>
      <div className="grid finance-grid finance-grid--entry">
        <Card title={t('finance.expenseCategories')}>
          <div className="form-row">
            <Input
              placeholder={t('finance.categoryName')}
              value={categoryName}
              onChange={(event) => setCategoryName(event.target.value)}
            />
            <PrimaryButton onClick={createCategory}>{t('finance.addCategory')}</PrimaryButton>
          </div>
          <ul className="pill-list">
            {isLoading
              ? Array.from({ length: 4 }).map((_, index) => (
                  <li key={`category-skeleton-${index}`} className="pill skeleton-pill" />
                ))
              : categories.map((category) => (
                  <li key={category.id} className="pill">
                    {category.name}
                  </li>
                ))}
          </ul>
        </Card>
        <Card title={t('finance.logExpense')}>
          <Input type="date" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} />
          <Input placeholder={t('finance.amount')} value={amount} onChange={(event) => setAmount(event.target.value)} />
          <Select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
            <option value="">{t('finance.category')}</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
          <Input
            placeholder={t('finance.paymentMethod')}
            value={paymentMethod}
            onChange={(event) => setPaymentMethod(event.target.value)}
          />
          <Input placeholder={t('finance.note')} value={note} onChange={(event) => setNote(event.target.value)} />
          <PrimaryButton onClick={createExpense}>{t('finance.saveExpense')}</PrimaryButton>
        </Card>
      </div>
      <div className="grid finance-grid">
        <Card
          title={t('finance.overviewTitle')}
          subtitle={t('finance.overviewSubtitle')}
          className="finance-card--wide"
        >
          {isLoading && !overview ? (
            <>
              <div className="table-wrapper">
                <table className="table table--skeleton">
                  <tbody>{renderSkeletonRows(3, 2)}</tbody>
                </table>
              </div>
              <div className="table-wrapper">
                <table className="table table--skeleton">
                  <tbody>{renderSkeletonRows(3, 3)}</tbody>
                </table>
              </div>
            </>
          ) : (
            overview && (
              <>
                <div className="table-wrapper">
                  <table className="table">
                    <tbody>
                      <tr>
                        <th scope="row">{t('finance.totalRevenue')}</th>
                        <td>{formatCurrency(overview.total_revenue)}</td>
                      </tr>
                      <tr>
                        <th scope="row">{t('finance.grossProfit')}</th>
                        <td>{formatCurrency(overview.gross_profit)}</td>
                      </tr>
                      <tr>
                        <th scope="row">{t('finance.totalTaxes')}</th>
                        <td>{formatCurrency(overview.total_taxes)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="table-wrapper">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>{t('finance.paymentMethodTitle')}</th>
                        <th>{t('finance.totalRevenue')}</th>
                        <th>{t('finance.totalTaxes')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paymentMethods.map((method) => (
                        <tr key={method}>
                          <td>{t(`finance.taxMethod.${method}`)}</td>
                          <td>{formatCurrency(overview.revenue_by_method?.[method])}</td>
                          <td>{formatCurrency(overview.taxes_by_method?.[method])}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )
          )}
        </Card>
        <Card title={t('finance.pnlSummary')}>
          {isLoading && !pnl ? (
            <div className="table-wrapper">
              <table className="table table--skeleton">
                <tbody>{renderSkeletonRows(5, 2)}</tbody>
              </table>
            </div>
          ) : (
            pnl && (
              <div className="table-wrapper">
                <table className="table">
                  <tbody>
                    <tr>
                      <th scope="row">{t('finance.totalSales')}</th>
                      <td>{formatCurrency(pnl.total_sales)}</td>
                    </tr>
                    <tr>
                      <th scope="row">{t('finance.cogs')}</th>
                      <td>{formatCurrency(pnl.cogs)}</td>
                    </tr>
                    <tr>
                      <th scope="row">{t('finance.grossProfit')}</th>
                      <td>{formatCurrency(pnl.gross_profit)}</td>
                    </tr>
                    <tr>
                      <th scope="row">{t('finance.expenses')}</th>
                      <td>{formatCurrency(pnl.expenses_total)}</td>
                    </tr>
                    <tr>
                      <th scope="row">{t('finance.netProfit')}</th>
                      <td>{formatCurrency(pnl.net_profit)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )
          )}
        </Card>
        <Card
          title={t('finance.topProductsTitle')}
          subtitle={t('finance.topProductsSubtitle')}
          className="finance-card--wide"
        >
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('finance.productName')}</th>
                  <th>{t('finance.quantity')}</th>
                  <th>{t('finance.totalRevenue')}</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && topRevenue.length === 0 ? (
                  renderSkeletonRows(4, 3)
                ) : topRevenue.length === 0 ? (
                  <tr>
                    <td colSpan={3}>{t('finance.noTopProducts')}</td>
                  </tr>
                ) : (
                  <>
                    {topRevenue.map((item) => (
                      <tr key={item.product_id}>
                        <td>{item.name}</td>
                        <td>{item.qty}</td>
                        <td>{formatCurrency(item.revenue)}</td>
                      </tr>
                    ))}
                    <tr>
                      <th colSpan={2}>{t('finance.totalRevenue')}</th>
                      <th>{formatCurrency(topRevenueTotal)}</th>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('finance.productName')}</th>
                  <th>{t('finance.quantity')}</th>
                  <th>{t('finance.totalMargin')}</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && topMargin.length === 0 ? (
                  renderSkeletonRows(4, 3)
                ) : topMargin.length === 0 ? (
                  <tr>
                    <td colSpan={3}>{t('finance.noTopProducts')}</td>
                  </tr>
                ) : (
                  <>
                    {topMargin.map((item) => (
                      <tr key={item.product_id}>
                        <td>{item.name}</td>
                        <td>{item.qty}</td>
                        <td>{formatCurrency(item.margin)}</td>
                      </tr>
                    ))}
                    <tr>
                      <th colSpan={2}>{t('finance.totalMargin')}</th>
                      <th>{formatCurrency(topMarginTotal)}</th>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title={t('finance.taxesTitle')} subtitle={t('finance.taxesSubtitle')} className="finance-card--wide">
          {isLoading && taxes.length === 0 ? (
            <div className="table-wrapper">
              <table className="table table--skeleton">
                <tbody>{renderSkeletonRows(4, 6)}</tbody>
              </table>
            </div>
          ) : taxes.length === 0 ? (
            <p>{t('finance.taxesEmpty')}</p>
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t('finance.taxName')}</th>
                    <th>{t('finance.taxRate')}</th>
                    <th>{t('finance.taxTotal')}</th>
                    <th>{t('finance.taxCash')}</th>
                    <th>{t('finance.taxCard')}</th>
                    <th>{t('finance.taxTransfer')}</th>
                  </tr>
                </thead>
                <tbody>
                  {taxes.map((tax) => (
                    <tr key={tax.rule_id}>
                      <td>{tax.name}</td>
                      <td>{tax.rate}</td>
                      <td>{formatCurrency(tax.total_tax)}</td>
                      <td>{formatCurrency(tax.by_method.cash)}</td>
                      <td>{formatCurrency(tax.by_method.card)}</td>
                      <td>{formatCurrency(tax.by_method.transfer)}</td>
                    </tr>
                  ))}
                  <tr>
                    <th colSpan={2}>{t('finance.taxGrandTotal')}</th>
                    <th>{formatCurrency(taxTotal)}</th>
                    <td colSpan={3}></td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </Card>
        <Card
          title={t('finance.inventoryTitle')}
          subtitle={t('finance.inventorySubtitle')}
          className="finance-card--wide"
        >
          {isLoading && !inventoryValuation ? (
            <>
              <span className="skeleton skeleton-text skeleton-text--wide" />
              <div className="table-wrapper">
                <table className="table table--skeleton">
                  <tbody>{renderSkeletonRows(4, 4)}</tbody>
                </table>
              </div>
            </>
          ) : (
            inventoryValuation && (
              <>
                <p>
                  <strong>{t('finance.inventoryTotal')}</strong> {formatCurrency(inventoryValuation.total_value)}
                </p>
                <div className="table-wrapper">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>{t('finance.productName')}</th>
                        <th>{t('finance.quantity')}</th>
                        <th>{t('finance.unitCost')}</th>
                        <th>{t('finance.inventoryValue')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inventoryValuation.items.length === 0 ? (
                        <tr>
                          <td colSpan={4}>{t('finance.inventoryEmpty')}</td>
                        </tr>
                      ) : (
                        inventoryValuation.items.map((item) => (
                          <tr key={item.product_id}>
                            <td>{item.name}</td>
                            <td>{item.qty_on_hand}</td>
                            <td>{formatCurrency(item.unit_cost)}</td>
                            <td>{formatCurrency(item.total_value)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )
          )}
        </Card>
        <Card title={t('finance.expensesTitle')} className="finance-card--wide">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('finance.expensesTitle')}</th>
                  <th>{t('finance.amount')}</th>
                  <th>{t('finance.note')}</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && expenses.length === 0
                  ? renderSkeletonRows(4, 3)
                  : expenses.map((expense) => (
                      <tr key={expense.id}>
                        <td>{new Date(expense.occurred_at).toLocaleDateString()}</td>
                        <td>{formatCurrency(expense.amount)}</td>
                        <td>{expense.note || t('finance.noNote')}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
