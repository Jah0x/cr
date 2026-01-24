import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'

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

  useEffect(() => {
    const lookup = async () => {
      if (!token) {
        setEmail(null)
        return
      }
      setError(null)
      try {
        const res = await api.get('/auth/invite-info', { params: { token } })
        setEmail(res.data.email)
      } catch (err) {
        setError(getApiErrorMessage(err, t, 'errors.inviteInvalid'))
      }
    }
    void lookup()
  }, [token])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    if (!token) {
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
      const res = await api.post('/auth/register-invite', { token, password })
      localStorage.setItem('token', res.data.access_token)
      navigate('/admin')
    } catch (err) {
      setError(getApiErrorMessage(err, t, 'errors.registrationFailed'))
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
