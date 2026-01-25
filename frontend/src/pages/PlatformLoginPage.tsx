import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'

export default function PlatformLoginPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      const res = await api.post('/platform/auth/login', { email, password })
      localStorage.setItem('platform_token', res.data.access_token)
      navigate('/platform/tenants')
    } catch (err) {
      setError(getApiErrorMessage(err, t, 'errors.invalidPlatformCredentials'))
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 480, margin: '0 auto' }}>
      <h2>{t('platformLogin.title')}</h2>
      <p>{t('platformLogin.subtitle')}</p>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input
          type="email"
          placeholder={t('login.emailPlaceholder')}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <input
          type="password"
          placeholder={t('login.passwordPlaceholder')}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <button type="submit" disabled={!email || !password}>
          {t('platformLogin.signIn')}
        </button>
      </form>
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
    </div>
  )
}
