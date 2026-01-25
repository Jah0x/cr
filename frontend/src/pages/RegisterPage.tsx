import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import axios from 'axios'

export default function RegisterPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [token, setToken] = useState(searchParams.get('token') ?? '')
  const [email, setEmail] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const getInviteErrorMessage = (err: unknown, fallbackKey: string): string => {
    if (axios.isAxiosError(err)) {
      const data = err.response?.data as { error?: { code?: string } } | undefined
      switch (data?.error?.code) {
        case 'INVITE_NOT_FOUND':
          return t('errors.inviteNotFound')
        case 'INVITE_EXPIRED':
          return t('errors.inviteExpired')
        case 'INVITE_TENANT_MISMATCH':
          return t('errors.inviteTenantMismatch')
        default:
          if (!err.response || typeof err.response.data === 'string' || err.response.status === 503) {
            return t('errors.inviteNetwork')
          }
      }
    }
    return getApiErrorMessage(err, t, fallbackKey)
  }

  useEffect(() => {
    const lookup = async () => {
      const trimmedToken = token.trim()
      if (!trimmedToken) {
        setEmail(null)
        setError(t('errors.inviteTokenMissing'))
        return
      }
      setError(null)
      try {
        const res = await api.get('/auth/invite-info', { params: { token: trimmedToken } })
        setEmail(res.data.email)
      } catch (err) {
        setError(getInviteErrorMessage(err, 'errors.inviteInvalid'))
      }
    }
    void lookup()
  }, [token, t])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    const trimmedToken = token.trim()
    if (!trimmedToken) {
      setError(t('errors.inviteTokenRequired'))
      return
    }
    if (password.length < 8) {
      setError(t('errors.passwordLength'))
      return
    }
    if (password !== confirm) {
      setError(t('errors.passwordMismatch'))
      return
    }
    setLoading(true)
    try {
      const res = await api.post('/auth/register-invite', { token: trimmedToken, password })
      localStorage.setItem('token', res.data.access_token)
      navigate('/admin')
    } catch (err) {
      setError(getInviteErrorMessage(err, 'errors.registrationFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 480, margin: '0 auto' }}>
      <h2>{t('register.title')}</h2>
      {email && (
        <p>
          {t('register.invitedEmail')}: <strong>{email}</strong>
        </p>
      )}
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input
          type="text"
          placeholder={t('register.inviteTokenPlaceholder')}
          value={token}
          onChange={(event) => setToken(event.target.value)}
        />
        <input
          type="password"
          placeholder={t('register.passwordPlaceholder')}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <input
          type="password"
          placeholder={t('register.confirmPasswordPlaceholder')}
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
        />
        <button type="submit" disabled={loading}>
          {t('register.setPassword')}
        </button>
      </form>
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
    </div>
  )
}
