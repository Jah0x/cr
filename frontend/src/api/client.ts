import axios from 'axios'
import { getApiBase } from '../config/runtimeConfig'
import i18n from '../i18n'

const api = axios.create({
  baseURL: getApiBase(),
  withCredentials: true,
  timeout: 15000
})

api.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  const token = localStorage.getItem('token')
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

    return Promise.reject(error)
  }
)

export default api
