import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function PlatformTenantCreatePage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [ownerPassword, setOwnerPassword] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [result, setResult] = useState<{ tenant_url?: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setResult(null)
    try {
      const res = await api.post('/platform/tenants', {
        name,
        code,
        owner_email: ownerEmail,
        owner_password: ownerPassword,
        template_id: templateId || null
      })
      setResult(res.data)
    } catch (err) {
      setError('Unable to create tenant.')
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 520 }}>
      <h2>Create tenant</h2>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <input placeholder="Tenant name" value={name} onChange={(event) => setName(event.target.value)} />
        <input placeholder="Tenant code" value={code} onChange={(event) => setCode(event.target.value)} />
        <input placeholder="Owner email" value={ownerEmail} onChange={(event) => setOwnerEmail(event.target.value)} />
        <input
          placeholder="Owner password"
          type="password"
          value={ownerPassword}
          onChange={(event) => setOwnerPassword(event.target.value)}
        />
        <input placeholder="Template id (optional)" value={templateId} onChange={(event) => setTemplateId(event.target.value)} />
        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit">Create</button>
          <button type="button" onClick={() => navigate('/platform/tenants')}>Cancel</button>
        </div>
      </form>
      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
      {result?.tenant_url && (
        <p style={{ marginTop: 12 }}>Tenant URL: <a href={result.tenant_url}>{result.tenant_url}</a></p>
      )}
    </div>
  )
}
