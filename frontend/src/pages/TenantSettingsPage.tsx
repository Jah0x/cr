import { useEffect, useMemo, useState } from 'react'
import {
  useTenantSettings,
  useUpdateFeatureSetting,
  useUpdateModuleSetting,
  useUpdateTenantSettings,
  useUpdateUIPrefs
} from '../api/tenantSettings'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

type PaymentMethod = 'cash' | 'card' | 'transfer'

type TaxRule = {
  id: string
  name: string
  rate: number
  is_active: boolean
  applies_to: PaymentMethod[]
}

type TaxSettings = {
  enabled: boolean
  mode: 'exclusive' | 'inclusive'
  rounding: 'round' | 'ceil' | 'floor'
  rules: TaxRule[]
}

const paymentMethods: PaymentMethod[] = ['cash', 'card', 'transfer']

const normalizePaymentMethod = (method: string): PaymentMethod => {
  if (method === 'external') return 'transfer'
  return method as PaymentMethod
}

const defaultTaxSettings: TaxSettings = {
  enabled: false,
  mode: 'exclusive',
  rounding: 'round',
  rules: []
}

export default function TenantSettingsPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const { data, isLoading, isError, error, refetch } = useTenantSettings()
  const updateModule = useUpdateModuleSetting()
  const updateFeature = useUpdateFeatureSetting()
  const updatePrefs = useUpdateUIPrefs()
  const [pendingPrefs, setPendingPrefs] = useState<Record<string, boolean>>({})
  const updateTenantSettings = useUpdateTenantSettings()
  const [taxDraft, setTaxDraft] = useState<TaxSettings>(defaultTaxSettings)
  const [newTaxName, setNewTaxName] = useState('')
  const [newTaxRate, setNewTaxRate] = useState('0')

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

  const storedTaxSettings = useMemo(() => {
    const settings = data.settings?.taxes
    if (!settings || typeof settings !== 'object') {
      return defaultTaxSettings
    }
    const rules = Array.isArray((settings as TaxSettings).rules) ? (settings as TaxSettings).rules : []
    return {
      ...defaultTaxSettings,
      ...(settings as Partial<TaxSettings>),
      rules: rules.map((rule) => ({
        ...rule,
        applies_to:
          Array.isArray(rule.applies_to) && rule.applies_to.length > 0
            ? rule.applies_to.map((method) => normalizePaymentMethod(method))
            : paymentMethods
      }))
    }
  }, [data.settings])

  const storedCurrency = useMemo(() => {
    const currency = data.settings?.currency
    if (typeof currency === 'string' && currency.trim()) {
      return currency
    }
    return 'RUB'
  }, [data.settings])

  useEffect(() => {
    setTaxDraft(storedTaxSettings)
  }, [storedTaxSettings])

  const [currency, setCurrency] = useState(storedCurrency)

  useEffect(() => {
    setCurrency(storedCurrency)
  }, [storedCurrency])

  const handlePrefToggle = (key: string) => {
    const currentValue = pendingPrefs[key] ?? data.ui_prefs[key] ?? false
    const next = { ...data.ui_prefs, ...pendingPrefs, [key]: !currentValue }
    setPendingPrefs(next)
    updatePrefs.mutate(next, {
      onSuccess: () => addToast(t('common.updated'), 'success'),
      onError: (err) => addToast(getApiErrorMessage(err, t, 'common.error'), 'error')
    })
  }

  const createTaxRuleId = () => {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      return crypto.randomUUID()
    }
    return `tax-${Date.now()}-${Math.random().toString(16).slice(2)}`
  }

  const saveTaxSettings = (next: TaxSettings) => {
    const invalidRule = next.rules.find((rule) => !rule.applies_to || rule.applies_to.length === 0)
    if (invalidRule) {
      addToast(t('settings.taxRuleApplyValidation'), 'error')
      return
    }
    updateTenantSettings.mutate(
      { taxes: next },
      {
        onSuccess: () => addToast(t('common.updated'), 'success'),
        onError: (err) => addToast(getApiErrorMessage(err, t, 'common.error'), 'error')
      }
    )
  }

  const handleTaxToggle = () => {
    const next = { ...taxDraft, enabled: !taxDraft.enabled }
    setTaxDraft(next)
    saveTaxSettings(next)
  }

  const handleTaxModeChange = (value: TaxSettings['mode']) => {
    const next = { ...taxDraft, mode: value }
    setTaxDraft(next)
    saveTaxSettings(next)
  }

  const handleTaxRoundingChange = (value: TaxSettings['rounding']) => {
    const next = { ...taxDraft, rounding: value }
    setTaxDraft(next)
    saveTaxSettings(next)
  }

  const handleTaxRuleToggle = (ruleId: string) => {
    const next = {
      ...taxDraft,
      rules: taxDraft.rules.map((rule) =>
        rule.id === ruleId ? { ...rule, is_active: !rule.is_active } : rule
      )
    }
    setTaxDraft(next)
    saveTaxSettings(next)
  }

  const handleTaxRuleRateChange = (ruleId: string, value: string) => {
    const rate = Number(value)
    if (Number.isNaN(rate) || rate < 0) return
    const next = {
      ...taxDraft,
      rules: taxDraft.rules.map((rule) => (rule.id === ruleId ? { ...rule, rate } : rule))
    }
    setTaxDraft(next)
  }

  const handleTaxRuleNameChange = (ruleId: string, value: string) => {
    const next = {
      ...taxDraft,
      rules: taxDraft.rules.map((rule) => (rule.id === ruleId ? { ...rule, name: value } : rule))
    }
    setTaxDraft(next)
  }

  const saveTaxRules = () => {
    saveTaxSettings(taxDraft)
  }

  const handleTaxRuleDelete = (ruleId: string) => {
    const next = { ...taxDraft, rules: taxDraft.rules.filter((rule) => rule.id !== ruleId) }
    setTaxDraft(next)
    saveTaxSettings(next)
  }

  const handleTaxRuleApplyToggle = (ruleId: string, method: PaymentMethod) => {
    const next = {
      ...taxDraft,
      rules: taxDraft.rules.map((rule) => {
        if (rule.id !== ruleId) return rule
        const nextAppliesTo = rule.applies_to.includes(method)
          ? rule.applies_to.filter((value) => value !== method)
          : [...rule.applies_to, method]
        if (nextAppliesTo.length === 0) {
          addToast(t('settings.taxRuleApplyValidation'), 'error')
          return rule
        }
        return { ...rule, applies_to: nextAppliesTo }
      })
    }
    setTaxDraft(next)
    saveTaxSettings(next)
  }

  const addTaxRule = () => {
    const rate = Number(newTaxRate)
    if (!newTaxName.trim() || Number.isNaN(rate) || rate < 0) {
      addToast(t('settings.taxRuleValidation'), 'error')
      return
    }
    const nextRule: TaxRule = {
      id: createTaxRuleId(),
      name: newTaxName.trim(),
      rate,
      is_active: true,
      applies_to: paymentMethods
    }
    const next = { ...taxDraft, rules: [...taxDraft.rules, nextRule] }
    setTaxDraft(next)
    setNewTaxName('')
    setNewTaxRate('0')
    saveTaxSettings(next)
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">{t('settings.title')}</h2>
        <p className="page-subtitle">{t('settings.subtitle')}</p>
      </div>
      <div className="grid grid-cards">
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
        <section className="card">
          <h3>{t('settings.currencyTitle')}</h3>
          <div className="form-stack">
            <label className="form-field">
              <span>{t('settings.currencyLabel')}</span>
              <select
                value={currency}
                disabled={updateTenantSettings.isPending}
                onChange={(event) => {
                  const next = event.target.value
                  setCurrency(next)
                  updateTenantSettings.mutate(
                    { currency: next },
                    {
                      onSuccess: () => addToast(t('common.updated'), 'success'),
                      onError: (err) => addToast(getApiErrorMessage(err, t, 'common.error'), 'error')
                    }
                  )
                }}
              >
                <option value="RUB">{t('settings.currencyRub')}</option>
                <option value="USD">{t('settings.currencyUsd')}</option>
                <option value="EUR">{t('settings.currencyEur')}</option>
              </select>
            </label>
          </div>
        </section>
        <section className="card">
          <h3>{t('settings.taxesTitle')}</h3>
          <p className="page-subtitle">{t('settings.taxesSubtitle')}</p>
          <div className="form-stack">
            <label className="form-inline">
              <input
                type="checkbox"
                checked={taxDraft.enabled}
                disabled={updateTenantSettings.isPending}
                onChange={handleTaxToggle}
              />
              <span>{t('settings.taxesEnabled')}</span>
            </label>
            <div className="form-row">
              <label className="form-field">
                <span>{t('settings.taxesMode')}</span>
                <select
                  value={taxDraft.mode}
                  disabled={updateTenantSettings.isPending}
                  onChange={(event) => handleTaxModeChange(event.target.value as TaxSettings['mode'])}
                >
                  <option value="exclusive">{t('settings.taxesModeExclusive')}</option>
                  <option value="inclusive">{t('settings.taxesModeInclusive')}</option>
                </select>
              </label>
              <label className="form-field">
                <span>{t('settings.taxesRounding')}</span>
                <select
                  value={taxDraft.rounding}
                  disabled={updateTenantSettings.isPending}
                  onChange={(event) => handleTaxRoundingChange(event.target.value as TaxSettings['rounding'])}
                >
                  <option value="round">{t('settings.taxesRoundingRound')}</option>
                  <option value="ceil">{t('settings.taxesRoundingCeil')}</option>
                  <option value="floor">{t('settings.taxesRoundingFloor')}</option>
                </select>
              </label>
            </div>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">{t('settings.taxRuleName')}</th>
                    <th scope="col">{t('settings.taxRuleRate')}</th>
                    <th scope="col">{t('settings.taxRuleMethods')}</th>
                    <th scope="col">{t('settings.taxRuleStatus')}</th>
                    <th scope="col">{t('settings.taxRuleActions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {taxDraft.rules.length === 0 ? (
                    <tr>
                      <td colSpan={5}>{t('settings.taxRuleEmpty')}</td>
                    </tr>
                  ) : (
                    taxDraft.rules.map((rule) => (
                      <tr key={rule.id}>
                        <td>
                          <input
                            value={rule.name}
                            onChange={(event) => handleTaxRuleNameChange(rule.id, event.target.value)}
                            onBlur={saveTaxRules}
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={rule.rate}
                            onChange={(event) => handleTaxRuleRateChange(rule.id, event.target.value)}
                            onBlur={saveTaxRules}
                          />
                        </td>
                        <td>
                          <div className="form-inline">
                            {paymentMethods.map((method) => (
                              <label key={method} className="form-inline">
                                <input
                                  type="checkbox"
                                  checked={rule.applies_to.includes(method)}
                                  onChange={() => handleTaxRuleApplyToggle(rule.id, method)}
                                />
                                <span>{t(`settings.taxRuleMethod.${method}`)}</span>
                              </label>
                            ))}
                          </div>
                        </td>
                        <td>
                          <label className="form-inline">
                            <input
                              type="checkbox"
                              checked={rule.is_active}
                              onChange={() => handleTaxRuleToggle(rule.id)}
                            />
                            <span>{rule.is_active ? t('settings.taxRuleActive') : t('settings.taxRuleInactive')}</span>
                          </label>
                        </td>
                        <td>
                          <button
                            className="secondary"
                            type="button"
                            onClick={() => handleTaxRuleDelete(rule.id)}
                          >
                            {t('common.delete')}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="form-row">
              <input
                placeholder={t('settings.taxRuleNamePlaceholder')}
                value={newTaxName}
                onChange={(event) => setNewTaxName(event.target.value)}
              />
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder={t('settings.taxRuleRatePlaceholder')}
                value={newTaxRate}
                onChange={(event) => setNewTaxRate(event.target.value)}
              />
              <button type="button" onClick={addTaxRule} disabled={updateTenantSettings.isPending}>
                {t('settings.addTaxRule')}
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
