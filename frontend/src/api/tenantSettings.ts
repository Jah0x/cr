import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from './client'

export type TenantModuleSetting = {
  code: string
  name: string
  description: string | null
  is_active: boolean
  is_enabled: boolean
}

export type TenantFeatureSetting = {
  code: string
  name: string
  description: string | null
  is_enabled: boolean
}

export type TenantSettingsResponse = {
  modules: TenantModuleSetting[]
  features: TenantFeatureSetting[]
  ui_prefs: Record<string, boolean>
}

export function useTenantSettings() {
  return useQuery({
    queryKey: ['tenantSettings'],
    queryFn: async () => {
      const res = await api.get<TenantSettingsResponse>('/tenant/settings')
      return res.data
    }
  })
}

export function useUpdateModuleSetting() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ code, is_enabled }: { code: string; is_enabled: boolean }) => {
      const res = await api.patch<TenantModuleSetting>(`/tenant/settings/modules/${code}`, { is_enabled })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenantSettings'] })
    }
  })
}

export function useUpdateFeatureSetting() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ code, is_enabled }: { code: string; is_enabled: boolean }) => {
      const res = await api.patch<TenantFeatureSetting>(`/tenant/settings/features/${code}`, { is_enabled })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenantSettings'] })
    }
  })
}

export function useUpdateUIPrefs() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (prefs: Record<string, boolean>) => {
      const res = await api.put<{ prefs: Record<string, boolean> }>(`/tenant/settings/ui-prefs`, { prefs })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenantSettings'] })
    }
  })
}
