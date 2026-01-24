import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'

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
  const { t } = useTranslation()
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

  const setPrimaryDomainMutation = useMutation({
    mutationFn: async (domainId: string) => {
      const res = await api.patch<TenantDomain>(`/platform/tenants/${tenant.id}/domains/${domainId}`)
      return res.data
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
          <div style={{ fontSize: 13, color: '#475569' }}>
            {t('platformTenants.codeLabel')}: {tenant.code}
          </div>
        </div>
        <button type="button" onClick={() => migrateMutation.mutate()} disabled={migrateMutation.isPending}>
          {migrateMutation.isPending ? t('platformTenants.migrating') : t('platformTenants.migrateTenant')}
        </button>
      </div>

      <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
        <label style={{ display: 'grid', gap: 4 }}>
          <span style={{ fontSize: 13, color: '#475569' }}>{t('platformTenants.tenantName')}</span>
          <input
            value={tenantName}
            onChange={(event) => setTenantName(event.target.value)}
            placeholder={t('platformTenants.tenantName')}
          />
        </label>
        <label style={{ display: 'grid', gap: 4 }}>
          <span style={{ fontSize: 13, color: '#475569' }}>{t('platformTenants.tenantCode')}</span>
          <input value={tenant.code} readOnly title={t('platformTenants.tenantCodeReadOnly')} />
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            checked={tenantStatus}
            onChange={(event) => setTenantStatus(event.target.checked)}
          />
          <span style={{ fontSize: 13, color: '#475569' }}>
            {t('common.status')}: {tenantStatus ? t('platformTenants.statusActive') : t('platformTenants.statusInactive')}
          </span>
        </label>
        <div>
          <button
            type="button"
            onClick={() => updateTenantMutation.mutate()}
            disabled={!tenantName || updateTenantMutation.isPending}
          >
            {updateTenantMutation.isPending ? t('common.saving') : t('common.save')}
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12, display: 'grid', gap: 4, fontSize: 13 }}>
        <div>{t('common.status')}: {status?.status ?? tenant.status}</div>
        <div>{t('common.schema')}: {status?.schema ?? tenant.code}</div>
        <div>{t('common.revision')}: {status?.revision || '—'}</div>
        <div>{t('common.head')}: {status?.head_revision || '—'}</div>
        <div>{t('platformTenants.schemaExists')}: {status?.schema_exists ? t('common.yes') : t('common.no')}</div>
        {status?.last_error && <div style={{ color: '#dc2626' }}>{t('platformTenants.lastError')}: {status.last_error}</div>}
      </div>

      <div style={{ marginTop: 16 }}>
        <h4 style={{ marginBottom: 8 }}>{t('platformTenants.domains')}</h4>
        <div style={{ display: 'grid', gap: 8 }}>
          {domains?.map((domain) => (
            <div
              key={domain.id}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <strong>{domain.domain}</strong>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input
                    type="radio"
                    name={`primary-domain-${tenant.id}`}
                    checked={domain.is_primary}
                    onChange={() => setPrimaryDomainMutation.mutate(domain.id)}
                    disabled={setPrimaryDomainMutation.isPending}
                  />
                  {t('common.primary')}
                </label>
              </div>
              <button type="button" onClick={() => deleteDomainMutation.mutate(domain.id)}>
                {t('common.remove')}
              </button>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
          <input
            placeholder={t('platformTenants.domainPlaceholder')}
            value={domainInput}
            onChange={(event) => setDomainInput(event.target.value)}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <input
              type="checkbox"
              checked={domainPrimary}
              onChange={(event) => setDomainPrimary(event.target.checked)}
            />
            {t('common.primary')}
          </label>
          <button
            type="button"
            onClick={() => createDomainMutation.mutate()}
            disabled={!domainInput || createDomainMutation.isPending}
          >
            {t('platformTenants.addDomain')}
          </button>
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <h4 style={{ marginBottom: 8 }}>{t('platformTenants.inviteLink')}</h4>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input
            placeholder={t('platformTenants.inviteEmailPlaceholder')}
            value={inviteEmail}
            onChange={(event) => setInviteEmail(event.target.value)}
          />
          <input
            placeholder={t('platformTenants.rolePlaceholder')}
            value={inviteRole}
            onChange={(event) => setInviteRole(event.target.value)}
          />
          <button type="button" onClick={() => inviteMutation.mutate()} disabled={!inviteEmail}>
            {t('platformTenants.generateInvite')}
          </button>
        </div>
        {inviteResult && (
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 13 }}>{t('platformTenants.expires')}: {inviteResult.expires_at}</div>
            <code style={{ display: 'block', wordBreak: 'break-all' }}>{inviteResult.invite_url}</code>
          </div>
        )}
      </div>

      <div style={{ marginTop: 16 }}>
        <h4 style={{ marginBottom: 8 }}>{t('platformTenants.users')}</h4>
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
                  {user.is_active ? t('platformTenants.deactivate') : t('platformTenants.activate')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (window.confirm(t('platformTenants.deleteUserConfirm'))) {
                      deleteUserMutation.mutate(user.id)
                    }
                  }}
                >
                  {t('platformTenants.delete')}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input
              placeholder={t('platformTenants.userEmail')}
              value={userEmail}
              onChange={(event) => setUserEmail(event.target.value)}
            />
            <input
              placeholder={t('platformTenants.rolesPlaceholder')}
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
              {t('platformTenants.passwordMode')}
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="radio"
                name={`user-mode-${tenant.id}`}
                checked={userMode === 'invite'}
                onChange={() => setUserMode('invite')}
              />
              {t('platformTenants.inviteMode')}
            </label>
            {userMode === 'password' && (
              <input
                placeholder={t('platformTenants.passwordPlaceholder')}
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
            {userMode === 'invite' ? t('platformTenants.createInvite') : t('platformTenants.addUser')}
          </button>
          {userInviteResult && userMode === 'invite' && (
            <div>
              <div style={{ fontSize: 13 }}>{t('platformTenants.expires')}: {userInviteResult.expires_at}</div>
              <code style={{ display: 'block', wordBreak: 'break-all' }}>{userInviteResult.invite_url}</code>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function PlatformTenantsPage() {
  const { t } = useTranslation()
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
        <h2>{t('platformTenants.title')}</h2>
        <Link to="/platform/tenants/new">{t('platformTenants.createTenant')}</Link>
      </div>
      {isLoading && <p>{t('platformTenants.loading')}</p>}
      {error && <p>{getApiErrorMessage(error, t, 'errors.loadTenantsFailed')}</p>}
      <div style={{ display: 'grid', gap: 12 }}>
        {data?.map((tenant) => (
          <TenantCard key={tenant.id} tenant={tenant} />
        ))}
      </div>
    </div>
  )
}
