import axios from 'axios'
import { getApiBase } from '../config/runtimeConfig'
import i18n from '../i18n'

export type ShiftStatus = 'open' | 'closed'

export type ShiftPaymentMethod = 'cash' | 'card' | 'transfer'

export type ShiftOut = {
  id: string
  store_id: string
  cashier_id: string
  opened_at: string
  closed_at: string | null
  status: ShiftStatus
  opening_cash: number
  closing_cash: number | null
  note: string | null
}

type ShiftAggregates = {
  sales_count: number
  revenue_total: number
  tax_total: number
  profit_gross_total: number
  by_payment_type: Partial<Record<ShiftPaymentMethod, number>>
}

export type ShiftDetail = ShiftOut & {
  aggregates: ShiftAggregates
}

export type ShiftListFilters = {
  store_id?: string
  date_from?: string
  date_to?: string
  cashier_id?: string
  status?: ShiftStatus
}

const api = axios.create({
  baseURL: getApiBase(),
  withCredentials: true,
  timeout: 15000
})

const tenantTokenKey = 'token'
const platformTokenKey = 'platform_token'

const isPlatformRequest = (url?: string | null): boolean => {
  if (!url) {
    return false
  }
  return url.startsWith('/platform')
}

api.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  const tokenKey = isPlatformRequest(config.url) ? platformTokenKey : tenantTokenKey
  const token = localStorage.getItem(tokenKey)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      const status = error?.response?.status ?? 'unknown'
      const url = error?.config?.url ?? 'unknown'
      const responseData = error?.response?.data
      // eslint-disable-next-line no-console
      console.error('API error', { status, url, response: responseData })
    }

    const isTimeout = error?.code === 'ECONNABORTED' || /timeout/i.test(error?.message ?? '')
    const isAbort = error?.code === 'ERR_CANCELED'

    if (isTimeout || isAbort) {
      const reason = isTimeout ? i18n.t('errors.requestTimeout') : i18n.t('errors.requestCancelled')
      const normalizedError = new Error(reason)
      normalizedError.cause = error
      return Promise.reject(normalizedError)
    }

    const status = error?.response?.status
    const url = error?.config?.url
    if (status === 401 && isPlatformRequest(url)) {
      localStorage.removeItem(platformTokenKey)
      if (window.location.pathname !== '/platform/login') {
        window.location.assign('/platform/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api

export const getShifts = async (filters: ShiftListFilters) => {
  const response = await api.get('/shifts', { params: filters })
  return response.data as ShiftOut[]
}

export const getShiftById = async (shiftId: string) => {
  const response = await api.get(`/shifts/${shiftId}`)
  return response.data as ShiftDetail
}

export const getActiveShift = async () => {
  const response = await api.get('/shifts/active')
  return response.data as ShiftOut | null
}

export const openShift = async (payload: { store_id: string; opening_cash?: number; note?: string }) => {
  const response = await api.post('/shifts', payload)
  return response.data as ShiftOut
}

export const closeShift = async (shiftId: string, payload: { closing_cash?: number; note?: string }) => {
  const response = await api.post(`/shifts/${shiftId}/close`, payload)
  return response.data as ShiftOut
}
