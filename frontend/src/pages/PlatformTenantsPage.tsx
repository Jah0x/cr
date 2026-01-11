import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

type Tenant = { id: string; name: string; code: string; status: string }

export default function PlatformTenantsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['platformTenants'],
    queryFn: async () => {
      const res = await api.get<Tenant[]>('/platform/tenants')
      return res.data
    }
  })

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Tenants</h2>
        <Link to="/platform/tenants/new">Create tenant</Link>
      </div>
      {isLoading && <p>Loading tenants...</p>}
      {error && <p>Unable to load tenants.</p>}
      <div style={{ display: 'grid', gap: 12 }}>
        {data?.map((tenant) => (
          <div key={tenant.id} style={{ border: '1px solid #e2e8f0', padding: 12, borderRadius: 8 }}>
            <div style={{ fontWeight: 600 }}>{tenant.name}</div>
            <div>Code: {tenant.code}</div>
            <div>Status: {tenant.status}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
