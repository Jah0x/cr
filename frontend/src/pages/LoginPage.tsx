import { useState } from 'react'
import api from '../api/client'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = async () => {
    try {
      const res = await api.post('/auth/login', { email, password })
      if (res.data?.access_token) {
        localStorage.setItem('token', res.data.access_token)
      }
      try {
        const me = await api.get('/auth/me')
        localStorage.setItem('user', JSON.stringify(me.data))
      } catch (meError) {
        console.warn('Failed to load current user', meError)
      }
      window.location.href = '/admin'
    } catch (e) {
      setError('Invalid credentials')
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: '80px auto', padding: 24, background: '#fff', borderRadius: 8 }}>
      <h2>Login</h2>
      <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%', marginBottom: 12 }} />
      <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: '100%', marginBottom: 12 }} />
      <button onClick={submit} style={{ width: '100%', padding: 12 }}>Sign in</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  )
}
