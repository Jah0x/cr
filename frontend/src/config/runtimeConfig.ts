export type RuntimeConfig = {
  platformHosts?: string[]
  rootDomain?: string
  apiBase?: string
}

const defaultApiBase = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
let runtimeConfig: RuntimeConfig | null = null

const normalizeHostList = (value: unknown): string[] | undefined => {
  if (!Array.isArray(value)) {
    return undefined
  }
  const hosts = value
    .map((host) => (typeof host === 'string' ? host.trim().toLowerCase() : ''))
    .filter(Boolean)
  return hosts.length > 0 ? hosts : undefined
}

const normalizeString = (value: unknown): string | undefined => {
  if (typeof value !== 'string') {
    return undefined
  }
  const trimmed = value.trim()
  return trimmed ? trimmed : undefined
}

const normalizeRuntimeConfig = (value: unknown): RuntimeConfig | null => {
  if (!value || typeof value !== 'object') {
    return null
  }
  const configValue = value as {
    platformHosts?: unknown
    rootDomain?: unknown
    apiBase?: unknown
  }
  const config: RuntimeConfig = {
    platformHosts: normalizeHostList(configValue.platformHosts),
    rootDomain: normalizeString(configValue.rootDomain),
    apiBase: normalizeString(configValue.apiBase)
  }
  return config
}

export const loadRuntimeConfig = async (): Promise<RuntimeConfig | null> => {
  try {
    const response = await fetch('/config.json', { cache: 'no-store' })
    if (!response.ok) {
      return null
    }
    const data = await response.json()
    runtimeConfig = normalizeRuntimeConfig(data)
    return runtimeConfig
  } catch (error) {
    return null
  }
}

export const getRuntimeConfig = (): RuntimeConfig | null => runtimeConfig

export const getApiBase = (): string => runtimeConfig?.apiBase ?? defaultApiBase
