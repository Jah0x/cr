import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

export default function PlatformTenantCreatePage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [result, setResult] = useState<{ tenant_url?: string; invite_url?: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setResult(null)
    setCopied(false)
    try {
      const res = await api.post('/platform/tenants', {
        name,
        code,
        owner_email: ownerEmail,
        template_id: templateId || null
      })
      setResult(res.data)
      addToast(t('common.created'), 'success')
    } catch (err) {
      const message = getApiErrorMessage(err, t, 'errors.createTenantFailed')
      setError(message)
      addToast(message, 'error')
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 520 }}>
      <h2>{t('platformTenantCreate.title')}</h2>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input placeholder={t('platformTenantCreate.tenantName')} value={name} onChange={(event) => setName(event.target.value)} />
        <input placeholder={t('platformTenantCreate.tenantCode')} value={code} onChange={(event) => setCode(event.target.value)} />
        <input placeholder={t('platformTenantCreate.ownerEmail')} value={ownerEmail} onChange={(event) => setOwnerEmail(event.target.value)} />
        <input placeholder={t('platformTenantCreate.templateId')} value={templateId} onChange={(event) => setTemplateId(event.target.value)} />
        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit">{t('common.create')}</button>
          <button type="button" onClick={() => navigate('/platform/tenants')}>{t('common.cancel')}</button>
        </div>
      </form>
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
      {result?.tenant_url && (
        <p style={{ marginTop: 12 }}>
          {t('platformTenantCreate.tenantUrl')}: <a href={result.tenant_url}>{result.tenant_url}</a>
        </p>
      )}
      {result?.invite_url && (
        <div style={{ marginTop: 12 }}>
          <div>{t('platformTenantCreate.inviteUrl')}:</div>
          <code style={{ display: 'block', wordBreak: 'break-all' }}>{result.invite_url}</code>
          <button
            type="button"
            onClick={async () => {
              if (result.invite_url) {
                await navigator.clipboard.writeText(result.invite_url)
                setCopied(true)
              }
            }}
            style={{ marginTop: 8 }}
          >
            {copied ? t('common.copied') : t('common.copy')}
          </button>
        </div>
      )}
    </div>
  )
}
