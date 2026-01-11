import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function PlatformLoginPage() {
  const [token, setToken] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    localStorage.setItem('token', token)
    navigate('/platform/tenants')
  }

  return (
    <div style={{ padding: 32, maxWidth: 480, margin: '0 auto' }}>
      <h2>Platform Access</h2>
      <p>Enter the bootstrap token to manage tenants.</p>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input
          type="password"
          placeholder="Bootstrap token"
          value={token}
          onChange={(event) => setToken(event.target.value)}
        />
        <button type="submit" disabled={!token}>Sign in</button>
      </form>
    </div>
  )
}
