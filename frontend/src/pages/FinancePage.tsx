import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

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

type PaymentMethod = 'cash' | 'card' | 'transfer'

type TaxReportItem = {
  rule_id: string
  name: string
  rate: number
  total_tax: number
  by_method: Partial<Record<PaymentMethod, number>>
}

const paymentMethods: PaymentMethod[] = ['cash', 'card', 'transfer']

const toDateParam = (value: string, endOfDay = false) => {
  if (!value) return undefined
  const date = new Date(`${value}T00:00:00`)
  if (endOfDay) {
    date.setHours(23, 59, 59, 999)
  }
  return date.toISOString()
}

export default function FinancePage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [categories, setCategories] = useState<ExpenseCategory[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [categoryName, setCategoryName] = useState('')
  const [occurredAt, setOccurredAt] = useState('')
  const [amount, setAmount] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [note, setNote] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [pnl, setPnl] = useState<PnlReport | null>(null)
  const [taxes, setTaxes] = useState<TaxReportItem[]>([])
  const [taxMethods, setTaxMethods] = useState<PaymentMethod[]>(paymentMethods)

  const params = useMemo(() => {
    return {
      date_from: toDateParam(dateFrom),
      date_to: toDateParam(dateTo, true)
    }
  }, [dateFrom, dateTo])

  const taxParams = useMemo(() => {
    const methods =
      taxMethods.length > 0 && taxMethods.length < paymentMethods.length ? taxMethods.join(',') : undefined
    return {
      ...params,
      methods
    }
  }, [params, taxMethods])

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

  const loadTaxes = async () => {
    const res = await api.get('/reports/taxes', { params: taxParams })
    setTaxes(res.data)
  }

  const loadData = async () => {
    try {
      await Promise.all([loadCategories(), loadExpenses(), loadPnl(), loadTaxes()])
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
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
    setDateFrom(start.toISOString().slice(0, 10))
    setDateTo(now.toISOString().slice(0, 10))
  }

  const toggleTaxMethod = (method: PaymentMethod) => {
    setTaxMethods((prev) => {
      if (prev.includes(method)) {
        return prev.filter((value) => value !== method)
      }
      return [...prev, method]
    })
  }

  const taxTotal = useMemo(() => {
    return taxes.reduce((sum, item) => sum + Number(item.total_tax || 0), 0)
  }, [taxes])

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">{t('finance.title')}</h2>
      </div>
      <div className="grid grid-cards">
        <section className="card">
          <h3>{t('finance.expenseCategories')}</h3>
          <div className="form-stack">
            <div className="form-row">
              <input
                placeholder={t('finance.categoryName')}
                value={categoryName}
                onChange={(event) => setCategoryName(event.target.value)}
              />
              <button onClick={createCategory}>{t('finance.addCategory')}</button>
            </div>
          </div>
          <ul className="pill-list">
            {categories.map((category) => (
              <li key={category.id} className="pill">{category.name}</li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h3>{t('finance.logExpense')}</h3>
          <div className="form-stack">
            <input type="date" value={occurredAt} onChange={(event) => setOccurredAt(event.target.value)} />
            <input placeholder={t('finance.amount')} value={amount} onChange={(event) => setAmount(event.target.value)} />
            <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
              <option value="">{t('finance.category')}</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            <input
              placeholder={t('finance.paymentMethod')}
              value={paymentMethod}
              onChange={(event) => setPaymentMethod(event.target.value)}
            />
            <input placeholder={t('finance.note')} value={note} onChange={(event) => setNote(event.target.value)} />
            <button onClick={createExpense}>{t('finance.saveExpense')}</button>
          </div>
        </section>
        <section className="card">
          <h3>{t('finance.pnlSummary')}</h3>
          <div className="form-inline">
            <button type="button" onClick={() => setQuickRange(1)}>{t('finance.today')}</button>
            <button type="button" onClick={() => setQuickRange(7)}>{t('finance.week')}</button>
            <button type="button" onClick={() => setQuickRange(30)}>{t('finance.month')}</button>
          </div>
          <div className="form-row">
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          {pnl && (
            <div className="table-wrapper">
              <table className="table">
                <tbody>
                  <tr>
                    <th scope="row">{t('finance.totalSales')}</th>
                    <td>{pnl.total_sales}</td>
                  </tr>
                  <tr>
                    <th scope="row">{t('finance.cogs')}</th>
                    <td>{pnl.cogs}</td>
                  </tr>
                  <tr>
                    <th scope="row">{t('finance.grossProfit')}</th>
                    <td>{pnl.gross_profit}</td>
                  </tr>
                  <tr>
                    <th scope="row">{t('finance.expenses')}</th>
                    <td>{pnl.expenses_total}</td>
                  </tr>
                  <tr>
                    <th scope="row">{t('finance.netProfit')}</th>
                    <td>{pnl.net_profit}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </section>
        <section className="card">
          <h3>{t('finance.taxesTitle')}</h3>
          <p className="page-subtitle">{t('finance.taxesSubtitle')}</p>
          <div className="form-inline">
            {paymentMethods.map((method) => (
              <label key={method} className="form-inline">
                <input
                  type="checkbox"
                  checked={taxMethods.includes(method)}
                  onChange={() => toggleTaxMethod(method)}
                />
                <span>{t(`finance.taxMethod.${method}`)}</span>
              </label>
            ))}
          </div>
          <div className="form-row">
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          {taxes.length === 0 ? (
            <p>{t('finance.taxesEmpty')}</p>
          ) : (
            <>
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
                        <td>{tax.total_tax}</td>
                        <td>{tax.by_method.cash ?? 0}</td>
                        <td>{tax.by_method.card ?? 0}</td>
                        <td>{tax.by_method.transfer ?? 0}</td>
                      </tr>
                    ))}
                    <tr>
                      <th colSpan={2}>{t('finance.taxGrandTotal')}</th>
                      <th>{taxTotal}</th>
                      <td colSpan={3}></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
        <section className="card">
          <h3>{t('finance.expensesTitle')}</h3>
          <div className="form-row">
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
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
                {expenses.map((expense) => (
                  <tr key={expense.id}>
                    <td>{new Date(expense.occurred_at).toLocaleDateString()}</td>
                    <td>{expense.amount}</td>
                    <td>{expense.note || t('finance.noNote')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
