import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

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
type TenantInviteItem = {
  id: string
  email: string
  created_at: string
  expires_at: string
  used_at?: string | null
}
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
  const { addToast } = useToast()
  const queryClient = useQueryClient()
  const [tenantName, setTenantName] = useState(tenant.name)
  const [tenantStatus, setTenantStatus] = useState(tenant.status === 'active')
  const [domainInput, setDomainInput] = useState('')
  const [domainPrimary, setDomainPrimary] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('owner')
  const [inviteResult, setInviteResult] = useState<TenantInvite | null>(null)
  const [regeneratedInvite, setRegeneratedInvite] = useState<TenantInvite | null>(null)
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
    queryFn: async () => (await api.get<TenantStatus>(`/platform/tenants/${tenant.id}/status`)).data
  })
  const { data: domains } = useQuery({
    queryKey: ['platformTenantDomains', tenant.id],
    queryFn: async () => (await api.get<TenantDomain[]>(`/platform/tenants/${tenant.id}/domains`)).data
  })
  const { data: users } = useQuery({
    queryKey: ['platformTenantUsers', tenant.id],
    queryFn: async () => (await api.get<TenantUser[]>(`/platform/tenants/${tenant.id}/users`)).data
  })
  const { data: invites } = useQuery({
    queryKey: ['platformTenantInvites', tenant.id],
    queryFn: async () => (await api.get<TenantInviteItem[]>(`/platform/tenants/${tenant.id}/invites`)).data
  })

  const roleList = useMemo(() => userRoles.split(',').map((role) => role.trim()).filter(Boolean), [userRoles])

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ['platformTenants'] })
    queryClient.invalidateQueries({ queryKey: ['platformTenantStatus', tenant.id] })
    queryClient.invalidateQueries({ queryKey: ['platformTenantDomains', tenant.id] })
    queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] })
    queryClient.invalidateQueries({ queryKey: ['platformTenantInvites', tenant.id] })
  }

  const migrateMutation = useMutation({
    mutationFn: async () => (await api.post<TenantStatus>(`/platform/tenants/${tenant.id}/migrate`)).data,
    onSuccess: () => { invalidateAll(); addToast(t('common.updated'), 'success') },
    onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  })

  const updateTenantMutation = useMutation({
    mutationFn: async () => (await api.patch<Tenant>(`/platform/tenants/${tenant.id}`, {
      name: tenantName,
      status: tenantStatus ? 'active' : 'inactive'
    })).data,
    onSuccess: () => { invalidateAll(); addToast(t('common.updated'), 'success') },
    onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  })

  const deleteTenantMutation = useMutation({
    mutationFn: async (dropSchema: boolean) => api.delete(`/platform/tenants/${tenant.id}?drop_schema=${dropSchema}`),
    onSuccess: (_data, dropSchema) => {
      queryClient.invalidateQueries({ queryKey: ['platformTenants'] })
      addToast(dropSchema ? t('platformTenants.deleteSuccess') : t('platformTenants.archiveSuccess'), 'success')
    },
    onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  })

  const createDomainMutation = useMutation({
    mutationFn: async () => (await api.post<TenantDomain>(`/platform/tenants/${tenant.id}/domains`, { domain: domainInput, is_primary: domainPrimary })).data,
    onSuccess: () => { setDomainInput(''); setDomainPrimary(false); queryClient.invalidateQueries({ queryKey: ['platformTenantDomains', tenant.id] }); addToast(t('common.created'), 'success') },
    onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  })
  const deleteDomainMutation = useMutation({ mutationFn: async (domainId: string) => api.delete(`/platform/tenants/${tenant.id}/domains/${domainId}`), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['platformTenantDomains', tenant.id] }); addToast(t('common.deleted'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const setPrimaryDomainMutation = useMutation({ mutationFn: async (domainId: string) => (await api.patch<TenantDomain>(`/platform/tenants/${tenant.id}/domains/${domainId}`)).data, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['platformTenantDomains', tenant.id] }); addToast(t('common.updated'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const inviteMutation = useMutation({ mutationFn: async () => (await api.post<TenantInvite>(`/platform/tenants/${tenant.id}/invite`, { email: inviteEmail, role_name: inviteRole })).data, onSuccess: (data) => { setInviteResult(data); addToast(t('common.created'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const regenerateInviteMutation = useMutation({ mutationFn: async (inviteId: string) => (await api.post<TenantInvite>(`/platform/tenants/${tenant.id}/invites/${inviteId}/regenerate`)).data, onSuccess: (data) => { setRegeneratedInvite(data); queryClient.invalidateQueries({ queryKey: ['platformTenantInvites', tenant.id] }); addToast(t('common.updated'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const deleteInviteMutation = useMutation({ mutationFn: async (inviteId: string) => api.delete(`/platform/tenants/${tenant.id}/invites/${inviteId}`), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['platformTenantInvites', tenant.id] }); addToast(t('common.deleted'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const createUserMutation = useMutation({ mutationFn: async () => (await api.post<TenantUser>(`/platform/tenants/${tenant.id}/users`, { email: userEmail, role_names: roleList, password: userPassword })).data, onSuccess: () => { setUserEmail(''); setUserPassword(''); setUserInviteResult(null); queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] }); addToast(t('common.created'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const inviteUserMutation = useMutation({ mutationFn: async () => (await api.post<TenantInvite>(`/platform/tenants/${tenant.id}/invite`, { email: userEmail, role_name: roleList[0] || 'admin' })).data, onSuccess: (data) => { setUserInviteResult(data); addToast(t('common.created'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const updateUserMutation = useMutation({ mutationFn: async ({ userId, isActive }: { userId: string; isActive: boolean }) => (await api.patch<TenantUser>(`/platform/tenants/${tenant.id}/users/${userId}`, { is_active: isActive })).data, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] }); addToast(t('common.updated'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })
  const deleteUserMutation = useMutation({ mutationFn: async (userId: string) => api.delete(`/platform/tenants/${tenant.id}/users/${userId}`), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['platformTenantUsers', tenant.id] }); addToast(t('common.deleted'), 'success') }, onError: (error) => addToast(getApiErrorMessage(error, t, 'common.error'), 'error') })

  const resolvedStatus = status?.status ?? tenant.status
  const resolvedStatusLabel = (() => {
    switch (resolvedStatus) {
      case 'active':
        return t('platformTenants.statusActive')
      case 'inactive':
      case 'provisioning':
        return t('platformTenants.statusProvisioning')
      case 'provisioning_failed':
      case 'error':
        return t('platformTenants.statusError')
      case 'archived':
        return t('platformTenants.statusArchived')
      default:
        return t('platformTenants.statusUnknown')
    }
  })()

  return (
    <article className="platform-org-card">
      <div className="platform-org-card__header">
        <div>
          <div className="platform-org-card__title">{tenantName} ({tenant.code})</div>
          <div className="platform-org-card__status">{t('common.status')}: {resolvedStatusLabel}</div>
        </div>
        <button type="button" onClick={() => migrateMutation.mutate()} disabled={migrateMutation.isPending}>
          {migrateMutation.isPending ? t('platformTenants.migrating') : t('platformTenants.migrateTenant')}
        </button>
      </div>

      <div className="platform-org-grid">
        <section>
          <h4>{t('platformTenants.sectionGeneral')}</h4>
          <div className="form-stack">
            <label className="form-field"><span>{t('platformTenants.tenantName')}</span><input value={tenantName} onChange={(event) => setTenantName(event.target.value)} /></label>
            <label className="form-field"><span>{t('platformTenants.tenantCode')}</span><input value={tenant.code} readOnly title={t('platformTenants.tenantCodeReadOnly')} /></label>
            <label className="form-inline"><input type="checkbox" checked={tenantStatus} onChange={(event) => setTenantStatus(event.target.checked)} /><span>{t('common.status')}: {tenantStatus ? t('platformTenants.statusActive') : t('platformTenants.statusInactive')}</span></label>
            <div className="form-inline">
              <button type="button" onClick={() => updateTenantMutation.mutate()} disabled={!tenantName || updateTenantMutation.isPending}>{updateTenantMutation.isPending ? t('common.saving') : t('common.save')}</button>
              <button
                type="button"
                className="danger"
                onClick={() => {
                  if (!window.confirm(t('platformTenants.deleteConfirm'))) return
                  const dropSchema = window.confirm(t('platformTenants.deleteDropSchemaConfirm'))
                  deleteTenantMutation.mutate(dropSchema)
                }}
                disabled={deleteTenantMutation.isPending}
              >
                {t('platformTenants.deleteOrganization')}
              </button>
            </div>
          </div>
        </section>

        <section>
          <h4>{t('platformTenants.sectionTech')}</h4>
          <div className="platform-org-tech">
            <div>{t('common.schema')}: {status?.schema ?? tenant.code}</div>
            <div>{t('common.revision')}: {status?.revision || '—'}</div>
            <div>{t('common.head')}: {status?.head_revision || '—'}</div>
            <div>{t('platformTenants.schemaExists')}: {status?.schema_exists ? t('common.yes') : t('common.no')}</div>
            {status?.last_error && <div style={{ color: '#dc2626' }}>{t('platformTenants.lastError')}: {status.last_error}</div>}
          </div>
        </section>
      </div>

      <section><h4>{t('platformTenants.domains')}</h4>{domains?.map((domain) => <div key={domain.id} className="platform-org-list-row"><div><strong>{domain.domain}</strong><label className="form-inline"><input type="radio" name={`primary-domain-${tenant.id}`} checked={domain.is_primary} onChange={() => setPrimaryDomainMutation.mutate(domain.id)} disabled={setPrimaryDomainMutation.isPending} />{t('common.primary')}</label></div><button type="button" onClick={() => deleteDomainMutation.mutate(domain.id)}>{t('common.remove')}</button></div>)}<div className="form-inline"><input placeholder={t('platformTenants.domainPlaceholder')} value={domainInput} onChange={(event) => setDomainInput(event.target.value)} /><label className="form-inline"><input type="checkbox" checked={domainPrimary} onChange={(event) => setDomainPrimary(event.target.checked)} />{t('common.primary')}</label><button type="button" onClick={() => createDomainMutation.mutate()} disabled={!domainInput || createDomainMutation.isPending}>{t('platformTenants.addDomain')}</button></div></section>

      <section><h4>{t('platformTenants.inviteLink')}</h4><div className="form-inline"><input placeholder={t('platformTenants.inviteEmailPlaceholder')} value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} /><input placeholder={t('platformTenants.rolePlaceholder')} value={inviteRole} onChange={(event) => setInviteRole(event.target.value)} /><button type="button" onClick={() => inviteMutation.mutate()} disabled={!inviteEmail}>{t('platformTenants.generateInvite')}</button></div>{inviteResult && <div><div style={{ fontSize: 13 }}>{t('platformTenants.expires')}: {inviteResult.expires_at}</div><code style={{ display: 'block', wordBreak: 'break-all' }}>{inviteResult.invite_url}</code></div>}</section>

      <section><h4>{t('platformTenants.users')}</h4>{users?.map((user) => <div key={user.id} className="platform-org-list-row"><div><div>{user.email}</div><div style={{ fontSize: 12, color: '#64748b' }}>{user.roles.join(', ')}</div></div><div className="form-inline"><button type="button" onClick={() => updateUserMutation.mutate({ userId: user.id, isActive: !user.is_active })}>{user.is_active ? t('platformTenants.deactivate') : t('platformTenants.activate')}</button><button type="button" onClick={() => window.confirm(t('platformTenants.deleteUserConfirm')) && deleteUserMutation.mutate(user.id)}>{t('platformTenants.delete')}</button></div></div>)}<div className="form-stack"><div className="form-inline"><input placeholder={t('platformTenants.userEmail')} value={userEmail} onChange={(event) => setUserEmail(event.target.value)} /><input placeholder={t('platformTenants.rolesPlaceholder')} value={userRoles} onChange={(event) => setUserRoles(event.target.value)} /></div><div className="form-inline"><label className="form-inline"><input type="radio" name={`user-mode-${tenant.id}`} checked={userMode === 'password'} onChange={() => setUserMode('password')} />{t('platformTenants.passwordMode')}</label><label className="form-inline"><input type="radio" name={`user-mode-${tenant.id}`} checked={userMode === 'invite'} onChange={() => setUserMode('invite')} />{t('platformTenants.inviteMode')}</label>{userMode === 'password' && <input placeholder={t('platformTenants.passwordPlaceholder')} type="password" value={userPassword} onChange={(event) => setUserPassword(event.target.value)} />}</div><button type="button" onClick={() => (userMode === 'invite' ? inviteUserMutation.mutate() : createUserMutation.mutate())} disabled={!userEmail || roleList.length === 0 || (userMode === 'password' && !userPassword)}>{userMode === 'invite' ? t('platformTenants.createInvite') : t('platformTenants.addUser')}</button>{userInviteResult && userMode === 'invite' && <div><div style={{ fontSize: 13 }}>{t('platformTenants.expires')}: {userInviteResult.expires_at}</div><code style={{ display: 'block', wordBreak: 'break-all' }}>{userInviteResult.invite_url}</code></div>}</div></section>

      <section>
        <h4>{t('platformTenants.invites')}</h4>
        {invites?.length ? invites.map((invite) => (
          <div key={invite.id} className="platform-org-list-row">
            <div>
              <strong>{invite.email}</strong>
              <div style={{ fontSize: 12, color: '#64748b' }}>{invite.created_at} · {invite.expires_at} · {invite.used_at ?? '—'}</div>
            </div>
            <div className="form-inline">
              <button type="button" onClick={() => regenerateInviteMutation.mutate(invite.id)} disabled={regenerateInviteMutation.isPending}>{t('platformTenants.regenerateInvite')}</button>
              <button type="button" onClick={() => window.confirm(t('platformTenants.deleteInviteConfirm')) && deleteInviteMutation.mutate(invite.id)}>{t('platformTenants.deleteInvite')}</button>
            </div>
          </div>
        )) : <div style={{ fontSize: 13, color: '#64748b' }}>{t('platformTenants.noInvites')}</div>}
        {regeneratedInvite && <div><div style={{ fontSize: 13 }}>{t('platformTenants.expires')}: {regeneratedInvite.expires_at}</div><code style={{ display: 'block', wordBreak: 'break-all' }}>{regeneratedInvite.invite_url}</code></div>}
      </section>
    </article>
  )
}

export default function PlatformTenantsPage() {
  const { t } = useTranslation()
  const { data, isLoading, error } = useQuery({
    queryKey: ['platformTenants'],
    queryFn: async () => (await api.get<Tenant[]>('/platform/tenants')).data
  })

  return (
    <div className="page">
      <div className="page-header-row">
        <h2>{t('platformTenants.title')}</h2>
        <Link to="/platform/tenants/new">{t('platformTenants.createTenant')}</Link>
      </div>
      {isLoading && <p>{t('platformTenants.loading')}</p>}
      {error && <p>{getApiErrorMessage(error, t, 'errors.loadTenantsFailed')}</p>}
      <div className="platform-org-cards">{data?.map((tenant) => <TenantCard key={tenant.id} tenant={tenant} />)}</div>
    </div>
  )
}
