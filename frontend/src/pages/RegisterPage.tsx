import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api/client'

export default function RegisterPage() {
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
        setError('Invite is invalid or expired.')
      }
    }
    void lookup()
  }, [token])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    if (!token) {
      setError('Invite token is required.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      const res = await api.post('/auth/register-invite', { token, password })
      localStorage.setItem('token', res.data.access_token)
      navigate('/admin')
    } catch (err) {
      setError('Unable to complete registration.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 32, maxWidth: 480, margin: '0 auto' }}>
      <h2>Complete registration</h2>
      {email && <p>Invited email: <strong>{email}</strong></p>}
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input
          type="text"
          placeholder="Invite token"
          value={token}
          onChange={(event) => setToken(event.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <input
          type="password"
          placeholder="Confirm password"
          value={confirm}
          onChange={(event) => setConfirm(event.target.value)}
        />
        <button type="submit" disabled={loading}>Set password</button>
      </form>
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
    </div>
  )
}
