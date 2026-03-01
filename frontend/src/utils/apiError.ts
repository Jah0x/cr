import axios from 'axios'
import type { TFunction } from 'i18next'

export const extractDetail = (error: unknown): string | undefined => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string; message?: string; error?: { message?: string } }
      | undefined
    return data?.detail ?? data?.message ?? data?.error?.message ?? error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return undefined
}

const extractRequestId = (error: unknown): string | undefined => {
  if (!axios.isAxiosError(error)) {
    return undefined
  }
  const headers = error.response?.headers
  const headerValue = headers?.['x-request-id'] ?? headers?.['X-Request-ID']
  const requestIdFromHeaders = Array.isArray(headerValue) ? headerValue[0] : headerValue
  if (requestIdFromHeaders) {
    return requestIdFromHeaders
  }
  const data = error.response?.data as
    | { request_id?: string; requestId?: string; requestID?: string }
    | undefined
  return data?.request_id ?? data?.requestId ?? data?.requestID
}

export const appendRequestId = (message: string, error: unknown, t: TFunction): string => {
  const requestId = extractRequestId(error)
  if (!requestId) {
    return message
  }
  return `${message} (${t('errors.requestId', { id: requestId })})`
}

export const getApiErrorMessage = (error: unknown, t: TFunction, fallbackKey: string): string => {
  const base = t(fallbackKey)
  const detail = extractDetail(error)
  const requestId = extractRequestId(error)
  let message = base

  if (import.meta.env.DEV && detail) {
    message = `${message} (${detail})`
  }

  if (requestId) {
    message = `${message} (${t('errors.requestId', { id: requestId })})`
  }

  return message
}
