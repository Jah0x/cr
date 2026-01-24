import { useState } from 'react'
import {
  useTenantSettings,
  useUpdateFeatureSetting,
  useUpdateModuleSetting,
  useUpdateUIPrefs
} from '../api/tenantSettings'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

export default function TenantSettingsPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const { data, isLoading, isError, error, refetch } = useTenantSettings()
  const updateModule = useUpdateModuleSetting()
  const updateFeature = useUpdateFeatureSetting()
  const updatePrefs = useUpdateUIPrefs()
  const [pendingPrefs, setPendingPrefs] = useState<Record<string, boolean>>({})

  if (isLoading) {
    return <div className="page">{t('settings.loading')}</div>
  }

  if (isError) {
    const message = getApiErrorMessage(error, t, 'errors.loadTenantSettingsMessage')
    return (
      <div className="page">
        <section className="card">
          <strong>{t('settings.errorTitle')}</strong>
          <div>{message}</div>
          <button type="button" onClick={() => refetch()}>
            {t('common.retry')}
          </button>
        </section>
      </div>
    )
  }

  if (!data) {
    return <div className="page">{t('settings.noSettings')}</div>
  }

  const uiPrefsFeatureEnabled =
    data.features.find((feature) => feature.code === 'ui_prefs')?.is_enabled ?? true

  const handlePrefToggle = (key: string) => {
    const currentValue = pendingPrefs[key] ?? data.ui_prefs[key] ?? false
    const next = { ...data.ui_prefs, ...pendingPrefs, [key]: !currentValue }
    setPendingPrefs(next)
    updatePrefs.mutate(next, {
      onSuccess: () => addToast(t('common.updated'), 'success'),
      onError: (err) => addToast(getApiErrorMessage(err, t, 'common.error'), 'error')
    })
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">{t('settings.title')}</h2>
        <p className="page-subtitle">{t('settings.subtitle')}</p>
      </div>
      <section className="card">
        <h3>{t('settings.modules')}</h3>
        <div className="form-stack">
          {data.modules.map((module) => (
            <label key={module.code} className="form-inline">
              <input
                type="checkbox"
                checked={module.is_active && module.is_enabled}
                disabled={!module.is_active || updateModule.isPending}
                onChange={() =>
                  updateModule.mutate(
                    { code: module.code, is_enabled: !module.is_enabled },
                    {
                      onSuccess: () => addToast(t('common.updated'), 'success'),
                      onError: (err) => addToast(getApiErrorMessage(err, t, 'common.error'), 'error')
                    }
                  )
                }
              />
              <span>
                {module.name} ({module.code}) {!module.is_active && `— ${t('settings.inactive')}`}
              </span>
            </label>
          ))}
        </div>
      </section>
      <section className="card">
        <h3>{t('settings.features')}</h3>
        <div className="form-stack">
          {data.features.map((feature) => (
            <label key={feature.code} className="form-inline">
              <input
                type="checkbox"
                checked={feature.is_enabled}
                disabled={updateFeature.isPending}
                onChange={() =>
                  updateFeature.mutate(
                    { code: feature.code, is_enabled: !feature.is_enabled },
                    {
                      onSuccess: () => addToast(t('common.updated'), 'success'),
                      onError: (err) => addToast(getApiErrorMessage(err, t, 'common.error'), 'error')
                    }
                  )
                }
              />
              <span>
                {feature.name} ({feature.code})
              </span>
            </label>
          ))}
        </div>
      </section>
      {uiPrefsFeatureEnabled && (
        <section className="card">
          <h3>{t('settings.uiPreferences')}</h3>
          <div className="form-stack">
            {[
              { key: 'compact_nav', label: t('settings.compactNav') },
              { key: 'show_help', label: t('settings.showHelp') }
            ].map(({ key, label }) => (
              <label key={key} className="form-inline">
                <input
                  type="checkbox"
                  checked={pendingPrefs[key] ?? data.ui_prefs[key] ?? false}
                  disabled={updatePrefs.isPending}
                  onChange={() => handlePrefToggle(key)}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
