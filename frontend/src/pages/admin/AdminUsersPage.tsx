import axios from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import type { TFunction } from 'i18next'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'
import Badge from '../../components/Badge'
import Card from '../../components/Card'
import { Button, PrimaryButton, SecondaryButton } from '../../components/Buttons'
import { Checkbox, Input } from '../../components/FormField'
import PageTitle from '../../components/PageTitle'

type Role = { id: string; name: string }

type User = { id: string; email: string; is_active: boolean; roles: Role[] }

const ROLE_ORDER = ['owner', 'manager', 'cashier'] as const

const getRoleOrder = (role: string) => {
  const index = ROLE_ORDER.indexOf(role as (typeof ROLE_ORDER)[number])
  return index === -1 ? ROLE_ORDER.length : index
}

type RoleModalProps = {
  user: User
  isBusy: boolean
  onClose: () => void
  onSubmit: (nextRoles: string[]) => void
  t: TFunction
}

const getRoleSelection = (user: User) => ({
  cashier: user.roles.some((role) => role.name === 'cashier'),
  manager: user.roles.some((role) => role.name === 'manager'),
  owner: user.roles.some((role) => role.name === 'owner')
})

function RoleAssignmentModal({ user, isBusy, onClose, onSubmit, t }: RoleModalProps) {
  const [roles, setRoles] = useState(() => getRoleSelection(user))

  useEffect(() => {
    setRoles(getRoleSelection(user))
  }, [user])

  const hasOwner = roles.owner
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextRoles = Object.entries(roles)
      .filter(([, checked]) => checked)
      .map(([role]) => role)
    onSubmit(nextRoles)
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <h4>{t('adminUsers.assignRoles', { defaultValue: 'Назначить роли' })}</h4>
          <Button variant="ghost" onClick={onClose} disabled={isBusy}>
            {t('common.cancel')}
          </Button>
        </div>
        <div className="muted">{user.email}</div>
        <form className="form-stack" onSubmit={handleSubmit}>
          <div className="form-stack">
            <span className="muted">{t('adminUsers.roles')}</span>
            <Checkbox
              checked={roles.cashier}
              disabled={isBusy || hasOwner}
              onChange={(event) => setRoles((prev) => ({ ...prev, cashier: event.target.checked }))}
              label="cashier"
            />
            <Checkbox
              checked={roles.manager}
              disabled={isBusy || hasOwner}
              onChange={(event) => setRoles((prev) => ({ ...prev, manager: event.target.checked }))}
              label="manager"
            />
            <Checkbox checked={roles.owner} disabled label="owner" />
            {hasOwner && (
              <span className="muted">
                {t('adminUsers.ownerLocked', { defaultValue: 'Owner роли нельзя менять' })}
              </span>
            )}
          </div>
          <div className="form-row">
            <PrimaryButton type="submit" disabled={isBusy || hasOwner}>
              {t('common.save', { defaultValue: 'Сохранить' })}
            </PrimaryButton>
            <Button type="button" variant="ghost" onClick={onClose} disabled={isBusy}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

type PasswordModalProps = {
  user: User
  isBusy: boolean
  onClose: () => void
  onSubmit: (password: string) => void
  t: TFunction
}

function PasswordUpdateModal({ user, isBusy, onClose, onSubmit, t }: PasswordModalProps) {
  const [password, setPassword] = useState('')

  useEffect(() => {
    setPassword('')
  }, [user])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit(password)
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="modal-header">
          <h4>{t('adminUsers.setPassword')}</h4>
          <Button variant="ghost" onClick={onClose} disabled={isBusy}>
            {t('common.cancel')}
          </Button>
        </div>
        <div className="muted">{user.email}</div>
        <form className="form-stack" onSubmit={handleSubmit}>
          <Input
            type="password"
            placeholder={t('adminUsers.newPasswordPlaceholder')}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={isBusy}
          />
          <div className="form-row">
            <PrimaryButton type="submit" disabled={isBusy}>
              {t('adminUsers.setPassword')}
            </PrimaryButton>
            <Button type="button" variant="ghost" onClick={onClose} disabled={isBusy}>
              {t('common.cancel')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminUsersPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [busyUsers, setBusyUsers] = useState<Record<string, boolean>>({})
  const [createOpen, setCreateOpen] = useState(false)
  const [createEmail, setCreateEmail] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createAutoPassword, setCreateAutoPassword] = useState(false)
  const [createRoles, setCreateRoles] = useState({ cashier: false, manager: false, owner: false })
  const [createActive, setCreateActive] = useState(true)
  const [creatingUser, setCreatingUser] = useState(false)
  const [roleModalUser, setRoleModalUser] = useState<User | null>(null)
  const [passwordModalUser, setPasswordModalUser] = useState<User | null>(null)

  const setUserBusy = (userId: string, isBusy: boolean) => {
    setBusyUsers((prev) => ({ ...prev, [userId]: isBusy }))
  }

  const updateUserState = (updated: User) => {
    setUsers((prev) => prev.map((user) => (user.id === updated.id ? updated : user)))
  }

  const handleApiError = (error: unknown) => {
    addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  }

  const getErrorDetail = (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const data = error.response?.data as
        | { detail?: string; message?: string; error?: { message?: string } }
        | undefined
      return data?.detail ?? data?.message ?? data?.error?.message ?? error.message
    }
    if (error instanceof Error) {
      return error.message
    }
    return undefined
  }

  const handleCreateError = (error: unknown) => {
    const detail = getErrorDetail(error)?.toLowerCase()
    if (detail && detail.includes('email') && (detail.includes('exists') || detail.includes('already'))) {
      addToast(
        t('adminUsers.emailExists', { defaultValue: 'Пользователь с таким email уже существует' }),
        'error'
      )
      return
    }
    handleApiError(error)
  }

  const loadUsers = async () => {
    setLoading(true)
    try {
      const res = await api.get<User[]>('/users')
      setUsers(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [])

  const generatePassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*'
    return Array.from({ length: 12 }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
  }

  const resetCreateForm = () => {
    setCreateEmail('')
    setCreatePassword('')
    setCreateAutoPassword(false)
    setCreateRoles({ cashier: false, manager: false, owner: false })
    setCreateActive(true)
  }

  const openCreateModal = () => {
    resetCreateForm()
    setCreateOpen(true)
  }

  const closeCreateModal = () => {
    setCreateOpen(false)
    resetCreateForm()
  }

  const handleCreateSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmedEmail = createEmail.trim()
    if (!trimmedEmail) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    let password = createPassword
    if (createAutoPassword && !password) {
      password = generatePassword()
      setCreatePassword(password)
    }
    if (!password) {
      addToast(t('adminUsers.passwordRequired'), 'error')
      return
    }
    if (password.length < 8) {
      addToast(t('errors.passwordLength'), 'error')
      return
    }
    const roles = Object.entries(createRoles)
      .filter(([role, checked]) => checked && role !== 'owner')
      .map(([role]) => role)
    setCreatingUser(true)
    try {
      await api.post<User>('/users', {
        email: trimmedEmail,
        password,
        roles,
        is_active: createActive
      })
      addToast(t('adminUsers.userCreated', { defaultValue: 'Пользователь создан' }), 'success')
      closeCreateModal()
      loadUsers()
    } catch (error) {
      handleCreateError(error)
    } finally {
      setCreatingUser(false)
    }
  }

  const updateRoles = async (user: User, nextRoles: string[]) => {
    setUserBusy(user.id, true)
    try {
      const res = await api.post<User>(`/users/${user.id}/roles`, { roles: nextRoles })
      updateUserState(res.data)
      addToast(t('adminUsers.rolesUpdated'), 'success')
      return true
    } catch (error) {
      handleApiError(error)
      return false
    } finally {
      setUserBusy(user.id, false)
    }
  }

  const handleRoleSubmit = async (user: User, nextRoles: string[]) => {
    const updated = await updateRoles(user, nextRoles)
    if (updated) {
      setRoleModalUser(null)
    }
  }

  const handlePasswordSubmit = async (user: User, password: string) => {
    if (!password) {
      addToast(t('adminUsers.passwordRequired'), 'error')
      return
    }
    if (password.length < 8) {
      addToast(t('errors.passwordLength'), 'error')
      return
    }
    setUserBusy(user.id, true)
    try {
      const res = await api.post<User>(`/users/${user.id}/password`, { password })
      updateUserState(res.data)
      addToast(t('adminUsers.passwordUpdated'), 'success')
      setPasswordModalUser(null)
    } catch (error) {
      handleApiError(error)
    } finally {
      setUserBusy(user.id, false)
    }
  }

  return (
    <div className="admin-page">
      <PageTitle
        title={t('adminNav.users')}
        subtitle={t('adminUsers.subtitle')}
        actions={
          <PrimaryButton type="button" onClick={openCreateModal}>
            {t('adminUsers.createUser', { defaultValue: 'Создать пользователя' })}
          </PrimaryButton>
        }
      />
      <Card>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{t('common.email')}</th>
                <th scope="col">{t('adminUsers.roles')}</th>
                <th scope="col">{t('adminUsers.active')}</th>
                <th scope="col">{t('admin.table.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4}>{t('common.loading')}</td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={4}>{t('adminUsers.empty')}</td>
                </tr>
              ) : (
                users.map((user) => {
                  const roleNames = user.roles.map((role) => role.name)
                  const sortedRoleNames = [...roleNames].sort(
                    (a, b) => getRoleOrder(a) - getRoleOrder(b)
                  )
                  const hasOwner = roleNames.includes('owner')
                  const isBusy = Boolean(busyUsers[user.id])
                  return (
                    <tr key={user.id}>
                      <td>{user.email}</td>
                      <td>
                        {roleNames.length === 0 ? (
                          <span className="muted">{t('adminUsers.noRoles')}</span>
                        ) : (
                          <div className="badge-list">
                            {sortedRoleNames.map((role) => (
                              <Badge key={role} variant="role">
                                {role}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </td>
                      <td>
                        <Badge variant={user.is_active ? 'default' : 'role'}>
                          {user.is_active ? t('common.yes') : t('common.no')}
                        </Badge>
                      </td>
                      <td>
                        <div className="form-stack">
                          <SecondaryButton type="button" onClick={() => setRoleModalUser(user)} disabled={isBusy}>
                            {t('adminUsers.assignRoles', { defaultValue: 'Назначить роли' })}
                          </SecondaryButton>
                          <SecondaryButton type="button" onClick={() => setPasswordModalUser(user)} disabled={isBusy}>
                            {t('adminUsers.setPassword')}
                          </SecondaryButton>
                          {hasOwner && (
                            <span className="muted">
                              {t('adminUsers.ownerLocked', { defaultValue: 'Owner роли нельзя менять' })}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {createOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('adminUsers.createUser', { defaultValue: 'Создать пользователя' })}</h4>
              <Button variant="ghost" onClick={closeCreateModal} disabled={creatingUser}>
                {t('common.cancel')}
              </Button>
            </div>
            <form className="form-stack" onSubmit={handleCreateSubmit}>
              <Input
                type="email"
                placeholder={t('common.email')}
                value={createEmail}
                onChange={(event) => setCreateEmail(event.target.value)}
                required
              />
              <div className="form-stack">
                <div className="form-inline">
                  <Input
                    type="password"
                    placeholder={t('adminUsers.newPasswordPlaceholder')}
                    value={createPassword}
                    onChange={(event) => {
                      setCreatePassword(event.target.value)
                      setCreateAutoPassword(false)
                    }}
                    disabled={createAutoPassword}
                  />
                  <SecondaryButton
                    type="button"
                    onClick={() => {
                      const generated = generatePassword()
                      setCreatePassword(generated)
                      setCreateAutoPassword(true)
                    }}
                  >
                    {t('adminUsers.generatePassword', { defaultValue: 'Сгенерировать' })}
                  </SecondaryButton>
                </div>
                <Checkbox
                  checked={createAutoPassword}
                  onChange={(event) => {
                    const nextValue = event.target.checked
                    setCreateAutoPassword(nextValue)
                    if (nextValue && !createPassword) {
                      setCreatePassword(generatePassword())
                    }
                  }}
                  label={t('adminUsers.autoPassword', { defaultValue: 'Автогенерация пароля' })}
                />
              </div>
              <div className="form-stack">
                <span className="muted">{t('adminUsers.roles')}</span>
                <Checkbox
                  checked={createRoles.cashier}
                  onChange={(event) => setCreateRoles((prev) => ({ ...prev, cashier: event.target.checked }))}
                  label="cashier"
                />
                <Checkbox
                  checked={createRoles.manager}
                  onChange={(event) => setCreateRoles((prev) => ({ ...prev, manager: event.target.checked }))}
                  label="manager"
                />
                <Checkbox checked={createRoles.owner} disabled label="owner" />
              </div>
              <Checkbox
                checked={createActive}
                onChange={(event) => setCreateActive(event.target.checked)}
                label={t('adminUsers.active')}
              />
              <div className="form-row">
                <PrimaryButton type="submit" disabled={creatingUser}>
                  {t('common.save', { defaultValue: 'Сохранить' })}
                </PrimaryButton>
                <Button type="button" variant="ghost" onClick={closeCreateModal} disabled={creatingUser}>
                  {t('common.cancel')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {roleModalUser && (
        <RoleAssignmentModal
          user={roleModalUser}
          isBusy={Boolean(busyUsers[roleModalUser.id])}
          onClose={() => setRoleModalUser(null)}
          onSubmit={(nextRoles) => handleRoleSubmit(roleModalUser, nextRoles)}
          t={t}
        />
      )}

      {passwordModalUser && (
        <PasswordUpdateModal
          user={passwordModalUser}
          isBusy={Boolean(busyUsers[passwordModalUser.id])}
          onClose={() => setPasswordModalUser(null)}
          onSubmit={(password) => handlePasswordSubmit(passwordModalUser, password)}
          t={t}
        />
      )}
    </div>
  )
}
