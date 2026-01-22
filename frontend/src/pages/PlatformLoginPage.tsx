import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function PlatformLoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      const res = await api.post('/platform/auth/login', { email, password })
      localStorage.setItem('token', res.data.access_token)
      navigate('/platform/tenants')
    } catch (err) {
      setError('Invalid platform credentials.')
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 480, margin: '0 auto' }}>
      <h2>Platform Access</h2>
      <p>Sign in with the platform owner credentials.</p>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <button type="submit" disabled={!email || !password}>Sign in</button>
      </form>
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
    </div>
  )
}
