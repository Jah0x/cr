import { useState } from 'react'
import {
  useTenantSettings,
  useUpdateFeatureSetting,
  useUpdateModuleSetting,
  useUpdateUIPrefs
} from '../api/tenantSettings'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'

export default function TenantSettingsPage() {
  const { t } = useTranslation()
  const { data, isLoading, isError, error, refetch } = useTenantSettings()
  const updateModule = useUpdateModuleSetting()
  const updateFeature = useUpdateFeatureSetting()
  const updatePrefs = useUpdateUIPrefs()
  const [pendingPrefs, setPendingPrefs] = useState<Record<string, boolean>>({})

  if (isLoading) {
    return <div style={{ padding: 24 }}>{t('settings.loading')}</div>
  }

  if (isError) {
    const message = getApiErrorMessage(error, t, 'errors.loadTenantSettingsMessage')
    return (
      <div style={{ padding: 24, display: 'grid', gap: 12 }}>
        <strong>{t('settings.errorTitle')}</strong>
        <div>{message}</div>
        <button type="button" onClick={() => refetch()}>
          {t('common.retry')}
        </button>
      </div>
    )
  }

  if (!data) {
    return <div style={{ padding: 24 }}>{t('settings.noSettings')}</div>
  }

  const uiPrefsFeatureEnabled =
    data.features.find((feature) => feature.code === 'ui_prefs')?.is_enabled ?? true

  const handlePrefToggle = (key: string) => {
    const currentValue = pendingPrefs[key] ?? data.ui_prefs[key] ?? false
    const next = { ...data.ui_prefs, ...pendingPrefs, [key]: !currentValue }
    setPendingPrefs(next)
    updatePrefs.mutate(next)
  }

  return (
    <div style={{ padding: 24, display: 'grid', gap: 24 }}>
      <div>
        <h2>{t('settings.title')}</h2>
        <p>{t('settings.subtitle')}</p>
      </div>
      <section style={{ display: 'grid', gap: 12 }}>
        <h3>{t('settings.modules')}</h3>
        {data.modules.map((module) => (
          <label key={module.code} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={module.is_active && module.is_enabled}
              disabled={!module.is_active || updateModule.isPending}
              onChange={() => updateModule.mutate({ code: module.code, is_enabled: !module.is_enabled })}
            />
            <span>
              {module.name} ({module.code}) {!module.is_active && `— ${t('settings.inactive')}`}
            </span>
          </label>
        ))}
      </section>
      <section style={{ display: 'grid', gap: 12 }}>
        <h3>{t('settings.features')}</h3>
        {data.features.map((feature) => (
          <label key={feature.code} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={feature.is_enabled}
              disabled={updateFeature.isPending}
              onChange={() => updateFeature.mutate({ code: feature.code, is_enabled: !feature.is_enabled })}
            />
            <span>
              {feature.name} ({feature.code})
            </span>
          </label>
        ))}
      </section>
      {uiPrefsFeatureEnabled && (
        <section style={{ display: 'grid', gap: 12 }}>
          <h3>{t('settings.uiPreferences')}</h3>
          {[
            { key: 'compact_nav', label: t('settings.compactNav') },
            { key: 'show_help', label: t('settings.showHelp') }
          ].map(({ key, label }) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={pendingPrefs[key] ?? data.ui_prefs[key] ?? false}
                disabled={updatePrefs.isPending}
                onChange={() => handlePrefToggle(key)}
              />
              <span>{label}</span>
            </label>
          ))}
        </section>
      )}
    </div>
  )
}
