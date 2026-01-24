import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

const TRANSLIT_MAP: Record<string, string> = {
  а: 'a',
  б: 'b',
  в: 'v',
  г: 'g',
  д: 'd',
  е: 'e',
  ё: 'e',
  ж: 'zh',
  з: 'z',
  и: 'i',
  й: 'i',
  к: 'k',
  л: 'l',
  м: 'm',
  н: 'n',
  о: 'o',
  п: 'p',
  р: 'r',
  с: 's',
  т: 't',
  у: 'u',
  ф: 'f',
  х: 'h',
  ц: 'ts',
  ч: 'ch',
  ш: 'sh',
  щ: 'shch',
  ы: 'y',
  э: 'e',
  ю: 'yu',
  я: 'ya',
  ъ: '',
  ь: ''
}

const slugify = (value: string) => {
  const transliterated = value
    .toLowerCase()
    .split('')
    .map((char) => TRANSLIT_MAP[char] ?? char)
    .join('')

  return transliterated
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-+|-+$/g, '')
}

export default function PlatformTenantCreatePage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [isCodeDirty, setIsCodeDirty] = useState(false)
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
        <label style={{ display: 'grid', gap: 6 }}>
          <input
            placeholder={t('platformTenantCreate.tenantName')}
            value={name}
            onChange={(event) => {
              const value = event.target.value
              setName(value)
              if (!isCodeDirty) {
                setCode(slugify(value))
              }
            }}
          />
          <span style={{ fontSize: 12, color: '#64748b' }}>name = отображаемое имя.</span>
        </label>
        <label style={{ display: 'grid', gap: 6 }}>
          <input
            placeholder={t('platformTenantCreate.tenantCode')}
            value={code}
            onChange={(event) => {
              setCode(event.target.value)
              setIsCodeDirty(true)
            }}
          />
          <span style={{ fontSize: 12, color: '#64748b' }}>code = slug (schema/subdomain).</span>
        </label>
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
