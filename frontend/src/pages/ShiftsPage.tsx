import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  closeShift,
  getShiftById,
  getShifts,
  type ShiftDetail,
  type ShiftListFilters,
  type ShiftOut,
  type ShiftStatus
} from '../api/client'
import api from '../api/client'
import Card from '../components/Card'
import { PrimaryButton, SecondaryButton } from '../components/Buttons'
import { Input, Select } from '../components/FormField'
import PageTitle from '../components/PageTitle'
import { getApiErrorMessage } from '../utils/apiError'

type CashierUser = {
  id: string
  email: string
  roles: Array<{ id: string; name: string }>
}

type ShiftFilters = {
  dateFrom: string
  dateTo: string
  cashierId: string
  storeId: string
  status: '' | ShiftStatus
}

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

const formatAmount = (value: number | string | null | undefined) => {
  const amount = Number(value ?? 0)
  return Number.isFinite(amount) ? amount.toFixed(2) : '0.00'
}

export default function ShiftsPage() {
  const { t, i18n } = useTranslation()
  const [shifts, setShifts] = useState<ShiftOut[]>([])
  const [cashiers, setCashiers] = useState<CashierUser[]>([])
  const [stores, setStores] = useState<Array<{ id: string; name: string }>>([])
  const [filters, setFilters] = useState<ShiftFilters>({
    dateFrom: '',
    dateTo: '',
    cashierId: '',
    storeId: '',
    status: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState('')
  const [selectedShift, setSelectedShift] = useState<ShiftDetail | null>(null)
  const [shiftDetails, setShiftDetails] = useState<Record<string, ShiftDetail>>({})

  const formatDateTime = (value: string | null) => {
    if (!value) return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return new Intl.DateTimeFormat(i18n.language || undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(date)
  }

  const cashierLabel = (cashierId: string) => cashiers.find((cashier) => cashier.id === cashierId)?.email ?? cashierId
  const storeLabel = (storeId: string) => stores.find((store) => store.id === storeId)?.name ?? storeId

  const paymentSummary = (shift: ShiftDetail) => {
    const byMethod = shift.aggregates?.by_payment_type ?? {}
    const cash = Number(byMethod.cash ?? 0)
    const card = Number(byMethod.card ?? 0)
    const transfer = Number(byMethod.transfer ?? 0)
    return `${formatAmount(cash)} / ${formatAmount(card)} / ${formatAmount(transfer)}`
  }

  const loadRefs = async () => {
    try {
      const [usersResponse, storesResponse] = await Promise.all([api.get('/users'), api.get('/stores')])
      setCashiers(usersResponse.data as CashierUser[])
      setStores(storesResponse.data as Array<{ id: string; name: string }>)
    } catch {
      setCashiers([])
      setStores([])
    }
  }

  const buildFilters = (): ShiftListFilters => {
    const params: ShiftListFilters = {}
    const dateFrom = toIsoDate(filters.dateFrom)
    const dateTo = toIsoDate(filters.dateTo, true)
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (filters.cashierId) params.cashier_id = filters.cashierId
    if (filters.storeId) params.store_id = filters.storeId
    if (filters.status) params.status = filters.status
    return params
  }

  const loadShifts = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getShifts(buildFilters())
      setShifts(data)
      const detailEntries = await Promise.all(
        data.map(async (shift) => {
          try {
            const detail = await getShiftById(shift.id)
            return [shift.id, detail] as const
          } catch {
            return null
          }
        })
      )
      setShiftDetails(
        detailEntries.reduce<Record<string, ShiftDetail>>((acc, entry) => {
          if (entry) {
            acc[entry[0]] = entry[1]
          }
          return acc
        }, {})
      )
    } catch (e) {
      setError(getApiErrorMessage(e, t, 'common.error'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadRefs()
    void loadShifts()
  }, [])

  const openDetails = async (shiftId: string) => {
    setDetailLoading(true)
    setDetailError('')
    setSelectedShift(null)
    try {
      const detail = await getShiftById(shiftId)
      setSelectedShift(detail)
    } catch (e) {
      setDetailError(getApiErrorMessage(e, t, 'common.error'))
    } finally {
      setDetailLoading(false)
    }
  }

  const closeActiveShift = async () => {
    if (!selectedShift || selectedShift.status !== 'open') return
    setDetailError('')
    try {
      const closed = await closeShift(selectedShift.id, {})
      setSelectedShift((prev) =>
        prev
          ? {
              ...prev,
              status: closed.status,
              closed_at: closed.closed_at,
              closing_cash: closed.closing_cash
            }
          : null
      )
      await loadShifts()
    } catch (e) {
      setDetailError(getApiErrorMessage(e, t, 'common.error'))
    }
  }

  const statusLabel = useMemo(
    () => ({
      open: t('shifts.statusOpen'),
      closed: t('shifts.statusClosed')
    }),
    [t]
  )

  return (
    <div className="page">
      <PageTitle title={t('shifts.title')} subtitle={t('shifts.subtitle')} />
      <Card title={t('shifts.filtersTitle')} className="form-stack">
        <div className="pos-history-filters">
          <label>
            <span>{t('shifts.filterDateFrom')}</span>
            <Input type="date" value={filters.dateFrom} onChange={(e) => setFilters((prev) => ({ ...prev, dateFrom: e.target.value }))} />
          </label>
          <label>
            <span>{t('shifts.filterDateTo')}</span>
            <Input type="date" value={filters.dateTo} onChange={(e) => setFilters((prev) => ({ ...prev, dateTo: e.target.value }))} />
          </label>
          <label>
            <span>{t('shifts.filterCashier')}</span>
            <Select value={filters.cashierId} onChange={(e) => setFilters((prev) => ({ ...prev, cashierId: e.target.value }))}>
              <option value="">{t('shifts.filterAllCashiers')}</option>
              {cashiers
                .filter((user) => user.roles.some((role) => role.name === 'cashier' || role.name === 'owner'))
                .map((cashier) => (
                  <option key={cashier.id} value={cashier.id}>
                    {cashier.email}
                  </option>
                ))}
            </Select>
          </label>
          <label>
            <span>{t('shifts.filterStore')}</span>
            <Select value={filters.storeId} onChange={(e) => setFilters((prev) => ({ ...prev, storeId: e.target.value }))}>
              <option value="">{t('shifts.filterAllStores')}</option>
              {stores.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name}
                </option>
              ))}
            </Select>
          </label>
          <label>
            <span>{t('shifts.filterStatus')}</span>
            <Select value={filters.status} onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value as '' | ShiftStatus }))}>
              <option value="">{t('shifts.filterAllStatuses')}</option>
              <option value="open">{t('shifts.statusOpen')}</option>
              <option value="closed">{t('shifts.statusClosed')}</option>
            </Select>
          </label>
        </div>
        <div className="pos-history-actions">
          <SecondaryButton
            onClick={() => {
              setFilters({ dateFrom: '', dateTo: '', cashierId: '', storeId: '', status: '' })
              setTimeout(() => void loadShifts(), 0)
            }}
          >
            {t('shifts.resetFilters')}
          </SecondaryButton>
          <PrimaryButton onClick={loadShifts}>{t('shifts.applyFilters')}</PrimaryButton>
        </div>
      </Card>

      <Card title={t('shifts.tableTitle')} className="pos-history" style={{ marginTop: 16 }}>
        {loading ? (
          <p className="page-subtitle">{t('common.loading')}</p>
        ) : error ? (
          <p className="pos-error">{error}</p>
        ) : shifts.length === 0 ? (
          <p className="page-subtitle">{t('shifts.empty')}</p>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>{t('shifts.colOpenedAt')}</th>
                  <th>{t('shifts.colClosedAt')}</th>
                  <th>{t('shifts.colCashier')}</th>
                  <th>{t('shifts.colStore')}</th>
                  <th>{t('shifts.colRevenue')}</th>
                  <th>{t('shifts.colPayments')}</th>
                  <th>{t('shifts.colStatus')}</th>
                  <th>{t('shifts.colAction')}</th>
                </tr>
              </thead>
              <tbody>
                {shifts.map((shift) => (
                  <tr key={shift.id}>
                    <td>{formatDateTime(shift.opened_at)}</td>
                    <td>{formatDateTime(shift.closed_at)}</td>
                    <td>{cashierLabel(shift.cashier_id)}</td>
                    <td>{storeLabel(shift.store_id)}</td>
                    <td>{formatAmount(shiftDetails[shift.id]?.aggregates.revenue_total)}</td>
                    <td>{shiftDetails[shift.id] ? paymentSummary(shiftDetails[shift.id]) : '—'}</td>
                    <td>{statusLabel[shift.status]}</td>
                    <td>
                      <ButtonAsLink onClick={() => void openDetails(shift.id)} label={t('shifts.details')} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selectedShift && (
        <Card title={t('shifts.detailTitle')} className="form-stack" style={{ marginTop: 16 }}>
          {detailLoading ? (
            <p className="page-subtitle">{t('common.loading')}</p>
          ) : detailError ? (
            <p className="pos-error">{detailError}</p>
          ) : (
            <>
              <div className="form-stack">
                <div>
                  <strong>{t('shifts.colOpenedAt')}:</strong> {formatDateTime(selectedShift.opened_at)}
                </div>
                <div>
                  <strong>{t('shifts.colClosedAt')}:</strong> {formatDateTime(selectedShift.closed_at)}
                </div>
                <div>
                  <strong>{t('shifts.colCashier')}:</strong> {cashierLabel(selectedShift.cashier_id)}
                </div>
                <div>
                  <strong>{t('shifts.colStatus')}:</strong> {statusLabel[selectedShift.status]}
                </div>
                <div>
                  <strong>{t('shifts.colRevenue')}:</strong> {formatAmount(selectedShift.aggregates.revenue_total)}
                </div>
                <div>
                  <strong>{t('shifts.colPayments')}:</strong> {paymentSummary(selectedShift)}
                </div>
              </div>
              {selectedShift.status === 'open' && (
                <div className="pos-history-actions">
                  <PrimaryButton onClick={closeActiveShift}>{t('shifts.closeShift')}</PrimaryButton>
                </div>
              )}
            </>
          )}
        </Card>
      )}
    </div>
  )
}

function ButtonAsLink({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button type="button" className="ghost" onClick={onClick}>
      {label}
    </button>
  )
}
