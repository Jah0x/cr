import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'

type Tenant = { id: string; name: string; code: string; status: string; last_error?: string | null }
type TenantStatus = {
  id: string
  name: string
  code: string
  status: string
  last_error?: string | null
  schema: string
  schema_exists: boolean
  revision?: string | null
  head_revision?: string | null
}
type TenantDomain = { id: string; domain: string; is_primary: boolean; created_at: string }
type TenantInvite = { invite_url: string; expires_at: string }
type TenantUser = {
  id: string
  email: string
  roles: string[]
  is_active: boolean
  created_at: string
  last_login_at?: string | null
}

function TenantCard({ tenant }: { tenant: Tenant }) {
  const queryClient = useQueryClient()
  const [tenantName, setTenantName] = useState(tenant.name)
  const [tenantStatus, setTenantStatus] = useState(tenant.status === 'active')
  const [domainInput, setDomainInput] = useState('')
  const [domainPrimary, setDomainPrimary] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('owner')
  const [inviteResult, setInviteResult] = useState<TenantInvite | null>(null)
  const [userEmail, setUserEmail] = useState('')
  const [userRoles, setUserRoles] = useState('admin')
  const [userPassword, setUserPassword] = useState('')
  const [userMode, setUserMode] = useState<'password' | 'invite'>('password')
  const [userInviteResult, setUserInviteResult] = useState<TenantInvite | null>(null)

  useEffect(() => {
    setTenantName(tenant.name)
    setTenantStatus(tenant.status === 'active')
  }, [tenant.name, tenant.status])

  const { data: status } = useQuery({
    queryKey: ['platformTenantStatus', tenant.id],
    queryFn: async () => {
      const res = await api.get<TenantStatus>(`/platform/tenants/${tenant.id}/status`)
      return res.data
    }
  })

  const { data: domains } = useQuery({
    queryKey: ['platformTenantDomains', tenant.id],
    queryFn: async () => {
      const res = await api.get<TenantDomain[]>(`/platform/tenants/${tenant.id}/domains`)
      return res.data
    }
  })

  const { data: users } = useQuery({
    queryKey: ['platformTenantUsers', tenant.id],
    queryFn: async () => {
      const res = await api.get<TenantUser[]>(`/platform/tenants/${tenant.id}/users`)
      return res.data
    }
  })

  const roleList = useMemo(
    () => userRoles.split(',').map((role) => role.trim()).filter(Boolean),
    [userRoles]
  )

  const migrateMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TenantStatus>(`/platform/tenants/${tenant.id}/migrate`)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platformTenantStatus', tenant.id] })
    }
  })

  const updateTenantMutation = useMutation({
    mutationFn: async () => {
      const res = await api.patch<Tenant>(`/platform/tenants/${tenant.id}`, {
        name: tenantName,
        status: tenantStatus ? 'active' : 'inactive'
      })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platformTenants'] })
      queryClient.invalidateQueries({ queryKey: ['platformTenantStatus', tenant.id] })
    }
  })

  const createDomainMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TenantDomain>(`/platform/tenants/${tenant.id}/domains`, {
        domain: domainInput,
        is_primary: domainPrimary
      })
      return res.data
    },
    onSuccess: () => {
      setDomainInput('')
      setDomainPrimary(false)
      queryClient.invalidateQueries({ queryKey: ['platformTenantDomains', tenant.id] })
    }
  })

  const deleteDomainMutation = useMutation({
    mutationFn: async (domainId: string) => {
      await api.delete(`/platform/tenants/${tenant.id}/domains/${domainId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platformTenantDomains', tenant.id] })
    }
  })

  const inviteMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TenantInvite>(`/platform/tenants/${tenant.id}/invite`, {
        email: inviteEmail,
        role_name: inviteRole
      })
      return res.data
    },
    onSuccess: (data) => {
      setInviteResult(data)
    }
  })

  const createUserMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TenantUser>(`/platform/tenants/${tenant.id}/users`, {
        email: userEmail,
        role_names: roleList,
        password: userPassword
      })
      return res.data
    },
    onSuccess: () => {
      setUserEmail('')
      setUserPassword('')
      setUserInviteResult(null)
      queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] })
    }
  })

  const inviteUserMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<TenantInvite>(`/platform/tenants/${tenant.id}/invite`, {
        email: userEmail,
        role_name: roleList[0] || 'admin'
      })
      return res.data
    },
    onSuccess: (data) => {
      setUserInviteResult(data)
    }
  })

  const updateUserMutation = useMutation({
    mutationFn: async ({ userId, isActive }: { userId: string; isActive: boolean }) => {
      const res = await api.patch<TenantUser>(`/platform/tenants/${tenant.id}/users/${userId}`, {
        is_active: isActive
      })
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] })
    }
  })

  const deleteUserMutation = useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/platform/tenants/${tenant.id}/users/${userId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] })
    }
  })

  return (
    <div style={{ border: '1px solid #e2e8f0', padding: 16, borderRadius: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 600 }}>{tenantName}</div>
          <div style={{ fontSize: 13, color: '#475569' }}>Code: {tenant.code}</div>
        </div>
        <button type="button" onClick={() => migrateMutation.mutate()} disabled={migrateMutation.isPending}>
          {migrateMutation.isPending ? 'Migrating...' : 'Migrate tenant'}
        </button>
      </div>

      <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
        <label style={{ display: 'grid', gap: 4 }}>
          <span style={{ fontSize: 13, color: '#475569' }}>Tenant name</span>
          <input
            value={tenantName}
            onChange={(event) => setTenantName(event.target.value)}
            placeholder="Tenant name"
          />
        </label>
        <label style={{ display: 'grid', gap: 4 }}>
          <span style={{ fontSize: 13, color: '#475569' }}>Tenant code</span>
          <input value={tenant.code} readOnly title="Tenant code cannot be edited." />
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            checked={tenantStatus}
            onChange={(event) => setTenantStatus(event.target.checked)}
          />
          <span style={{ fontSize: 13, color: '#475569' }}>
            Status: {tenantStatus ? 'active' : 'inactive'}
          </span>
        </label>
        <div>
          <button
            type="button"
            onClick={() => updateTenantMutation.mutate()}
            disabled={!tenantName || updateTenantMutation.isPending}
          >
            {updateTenantMutation.isPending ? 'Saving...' : 'Save tenant'}
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12, display: 'grid', gap: 4, fontSize: 13 }}>
        <div>Status: {status?.status ?? tenant.status}</div>
        <div>Schema: {status?.schema ?? tenant.code}</div>
        <div>Revision: {status?.revision || '—'}</div>
        <div>Head: {status?.head_revision || '—'}</div>
        <div>Schema exists: {status?.schema_exists ? 'Yes' : 'No'}</div>
        {status?.last_error && <div style={{ color: '#dc2626' }}>Last error: {status.last_error}</div>}
      </div>

      <div style={{ marginTop: 16 }}>
        <h4 style={{ marginBottom: 8 }}>Domains</h4>
        <div style={{ display: 'grid', gap: 8 }}>
          {domains?.map((domain) => (
            <div
              key={domain.id}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <strong>{domain.domain}</strong>
                {domain.is_primary && <span style={{ marginLeft: 8, color: '#0f766e' }}>primary</span>}
              </div>
              <button type="button" onClick={() => deleteDomainMutation.mutate(domain.id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
          <input
            placeholder="domain.example.com"
            value={domainInput}
            onChange={(event) => setDomainInput(event.target.value)}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <input
              type="checkbox"
              checked={domainPrimary}
              onChange={(event) => setDomainPrimary(event.target.checked)}
            />
            Primary
          </label>
          <button
            type="button"
            onClick={() => createDomainMutation.mutate()}
            disabled={!domainInput || createDomainMutation.isPending}
          >
            Add domain
          </button>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h4 style={{ marginBottom: 8 }}>Invite link</h4>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input
            placeholder="email@example.com"
            value={inviteEmail}
            onChange={(event) => setInviteEmail(event.target.value)}
          />
          <input
            placeholder="role"
            value={inviteRole}
            onChange={(event) => setInviteRole(event.target.value)}
          />
          <button type="button" onClick={() => inviteMutation.mutate()} disabled={!inviteEmail}>
            Generate invite
          </button>
        </div>
        {inviteResult && (
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 13 }}>Expires: {inviteResult.expires_at}</div>
            <code style={{ display: 'block', wordBreak: 'break-all' }}>{inviteResult.invite_url}</code>
          </div>
        )}
      </div>

      <div style={{ marginTop: 16 }}>
        <h4 style={{ marginBottom: 8 }}>Users</h4>
        <div style={{ display: 'grid', gap: 8 }}>
          {users?.map((user) => (
            <div
              key={user.id}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div>
                <div>{user.email}</div>
                <div style={{ fontSize: 12, color: '#64748b' }}>{user.roles.join(', ')}</div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  onClick={() => updateUserMutation.mutate({ userId: user.id, isActive: !user.is_active })}
                >
                  {user.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm('Delete this user?')) {
                      deleteUserMutation.mutate(user.id)
                    }
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input
              placeholder="user email"
              value={userEmail}
              onChange={(event) => setUserEmail(event.target.value)}
            />
            <input
              placeholder="roles (comma separated)"
              value={userRoles}
              onChange={(event) => setUserRoles(event.target.value)}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="radio"
                name={`user-mode-${tenant.id}`}
                checked={userMode === 'password'}
                onChange={() => setUserMode('password')}
              />
              Password
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="radio"
                name={`user-mode-${tenant.id}`}
                checked={userMode === 'invite'}
                onChange={() => setUserMode('invite')}
              />
              Invite
            </label>
            {userMode === 'password' && (
              <input
                placeholder="password"
                type="password"
                value={userPassword}
                onChange={(event) => setUserPassword(event.target.value)}
              />
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              if (userMode === 'invite') {
                inviteUserMutation.mutate()
              } else {
                createUserMutation.mutate()
              }
            }}
            disabled={!userEmail || roleList.length === 0 || (userMode === 'password' && !userPassword)}
          >
            {userMode === 'invite' ? 'Create invite' : 'Add user'}
          </button>
          {userInviteResult && userMode === 'invite' && (
            <div>
              <div style={{ fontSize: 13 }}>Expires: {userInviteResult.expires_at}</div>
              <code style={{ display: 'block', wordBreak: 'break-all' }}>{userInviteResult.invite_url}</code>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

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
          <TenantCard key={tenant.id} tenant={tenant} />
        ))}
      </div>
    </div>
  )
}
