import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useTranslation } from 'react-i18next'

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

  const params = useMemo(() => {
    return {
      date_from: toDateParam(dateFrom),
      date_to: toDateParam(dateTo, true)
    }
  }, [dateFrom, dateTo])

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

  const loadData = async () => {
    await Promise.all([loadCategories(), loadExpenses(), loadPnl()])
  }

  useEffect(() => {
    loadData()
  }, [params.date_from, params.date_to])

  const createCategory = async () => {
    if (!categoryName.trim()) return
    await api.post('/finance/expense-categories', { name: categoryName })
    setCategoryName('')
    loadCategories()
  }

  const createExpense = async () => {
    if (!occurredAt || !amount) return
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
    loadExpenses()
    loadPnl()
  }

  const setQuickRange = (days: number) => {
    const now = new Date()
    const start = new Date(now)
    start.setDate(now.getDate() - days + 1)
    setDateFrom(start.toISOString().slice(0, 10))
    setDateTo(now.toISOString().slice(0, 10))
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>{t('finance.title')}</h2>
      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('finance.expenseCategories')}</h3>
          <input
            placeholder={t('finance.categoryName')}
            value={categoryName}
            onChange={(event) => setCategoryName(event.target.value)}
          />
          <button onClick={createCategory}>{t('finance.addCategory')}</button>
          <ul>
            {categories.map((category) => (
              <li key={category.id}>{category.name}</li>
            ))}
          </ul>
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('finance.logExpense')}</h3>
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
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('finance.pnlSummary')}</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="button" onClick={() => setQuickRange(1)}>{t('finance.today')}</button>
            <button type="button" onClick={() => setQuickRange(7)}>{t('finance.week')}</button>
            <button type="button" onClick={() => setQuickRange(30)}>{t('finance.month')}</button>
          </div>
          <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          {pnl && (
            <div style={{ marginTop: 12 }}>
              <p>{t('finance.totalSales')}: {pnl.total_sales}</p>
              <p>{t('finance.cogs')}: {pnl.cogs}</p>
              <p>{t('finance.grossProfit')}: {pnl.gross_profit}</p>
              <p>{t('finance.expenses')}: {pnl.expenses_total}</p>
              <p>{t('finance.netProfit')}: {pnl.net_profit}</p>
            </div>
          )}
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('finance.expensesTitle')}</h3>
          <div style={{ display: 'grid', gap: 8 }}>
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          <ul>
            {expenses.map((expense) => (
              <li key={expense.id}>
                {new Date(expense.occurred_at).toLocaleDateString()} — {expense.amount} — {expense.note || t('finance.noNote')}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
