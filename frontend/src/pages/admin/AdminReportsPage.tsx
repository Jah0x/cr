import { useMemo, useState } from 'react'
import axios from 'axios'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'
import Card from '../../components/Card'
import { PrimaryButton } from '../../components/Buttons'
import { Input, Select } from '../../components/FormField'
import PageTitle from '../../components/PageTitle'

type ReportSummary = {
  total_sales?: number
  total_purchases?: number
  gross_margin?: number
  sales_count?: number
}

type FastApiValidationError = { loc?: Array<string | number>; msg: string; type?: string }

type ApiErrorPayload = { detail?: string | FastApiValidationError[]; message?: string }

type Period = 'today' | 'week' | 'month' | 'custom'

export default function AdminReportsPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [summary, setSummary] = useState<ReportSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [period, setPeriod] = useState<Period>('week')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const formatValidationErrors = (errors: FastApiValidationError[]) =>
    errors
      .map((item) => {
        if (item.loc?.length) {
          return `${item.loc.join('.')}: ${item.msg}`
        }
        return item.msg
      })
      .join(', ')

  const handleApiError = (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      if (status === 409) {
        addToast(t('admin.errors.alreadyExists'), 'error')
        return
      }
      if (status === 422) {
        const data = error.response?.data as ApiErrorPayload | undefined
        const detail = data?.detail ?? data?.message
        if (Array.isArray(detail)) {
          const message = formatValidationErrors(detail)
          addToast(message || t('common.error'), 'error')
          return
        }
        addToast(detail || t('common.error'), 'error')
        return
      }
      if (status === 500) {
        const data = error.response?.data as ApiErrorPayload | undefined
        const detail = data?.detail ?? data?.message
        if (typeof detail === 'string') {
          addToast(detail || t('common.error'), 'error')
          return
        }
        if (detail) {
          const safeDetail = typeof detail === 'object' ? JSON.stringify(detail) : String(detail)
          addToast(`Internal error: ${safeDetail}`, 'error')
          return
        }
        addToast(t('common.error'), 'error')
        return
      }
    }
    addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  }

  const loadSummary = async () => {
    setSummaryLoading(true)
    try {
      const res = await api.get('/reports/summary')
      setSummary(res.data)
      addToast(t('common.saved'), 'success')
    } catch (error) {
      handleApiError(error)
    } finally {
      setSummaryLoading(false)
    }
  }

  const kpiCards = useMemo(
    () => [
      { label: t('adminReports.revenue'), value: summary?.total_sales ?? '—' },
      { label: t('adminReports.purchases'), value: summary?.total_purchases ?? '—' },
      { label: t('adminReports.margin'), value: summary?.gross_margin ?? '—' },
      { label: t('adminReports.salesCount'), value: summary?.sales_count ?? '—' }
    ],
    [summary, t]
  )

  return (
    <div className="admin-page">
      <PageTitle title={t('adminNav.reports')} subtitle={t('adminReports.subtitle')} />

      <Card>
        <div className="form-stack">
          <div className="form-row">
            <Select label={t('adminReports.period')} value={period} onChange={(e) => setPeriod(e.target.value as Period)}>
              <option value="today">{t('finance.today')}</option>
              <option value="week">{t('finance.week')}</option>
              <option value="month">{t('finance.month')}</option>
              <option value="custom">{t('adminReports.customRange')}</option>
            </Select>
            <Input
              label={t('adminReports.from')}
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              disabled={period !== 'custom'}
            />
            <Input
              label={t('adminReports.to')}
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              disabled={period !== 'custom'}
            />
            <PrimaryButton onClick={loadSummary}>{t('adminReports.load')}</PrimaryButton>
          </div>
        </div>
      </Card>

      <section className="kpi-grid">
        {summaryLoading
          ? Array.from({ length: 4 }, (_, index) => (
              <div key={`kpi-skeleton-${index}`} className="card kpi-card" aria-hidden="true">
                <span className="skeleton skeleton-text" />
                <span className="skeleton skeleton-text skeleton-text--wide" />
              </div>
            ))
          : kpiCards.map((card) => (
              <div key={card.label} className="card kpi-card">
                <span className="muted">{card.label}</span>
                <strong>{card.value}</strong>
              </div>
            ))}
      </section>

      {!summaryLoading && !summary && (
        <div className="card">
          <div className="form-stack">
            <p className="page-subtitle">
              {t('adminReports.noSummary', { defaultValue: 'Сначала загрузите сводку отчета.' })}
            </p>
            <PrimaryButton onClick={loadSummary}>{t('adminReports.load')}</PrimaryButton>
          </div>
        </div>
      )}

      <section className="card">
        <div>
          <h3>{t('adminReports.topProducts')}</h3>
          <p className="page-subtitle">{t('adminReports.topProductsSubtitle')}</p>
        </div>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{t('admin.table.name')}</th>
                <th scope="col">{t('adminReports.sales')}</th>
                <th scope="col">{t('adminReports.revenue')}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={3}>{t('adminReports.noData')}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
