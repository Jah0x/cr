import axios from 'axios'
import type { TFunction } from 'i18next'

const extractDetail = (error: unknown): string | undefined => {
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

export const getApiErrorMessage = (error: unknown, t: TFunction, fallbackKey: string): string => {
  const base = t(fallbackKey)
  const detail = extractDetail(error)

  if (import.meta.env.DEV && detail) {
    return `${base} (${detail})`
  }

  return base
}
