import axios from 'axios'
import { useEffect, useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'

type Role = { id: string; name: string }

type User = { id: string; email: string; is_active: boolean; roles: Role[] }

const ROLE_ORDER = ['owner', 'manager', 'cashier'] as const

const getRoleOrder = (role: string) => {
  const index = ROLE_ORDER.indexOf(role as (typeof ROLE_ORDER)[number])
  return index === -1 ? ROLE_ORDER.length : index
}

export default function AdminUsersPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [busyUsers, setBusyUsers] = useState<Record<string, boolean>>({})
  const [passwords, setPasswords] = useState<Record<string, string>>({})
  const [createOpen, setCreateOpen] = useState(false)
  const [createEmail, setCreateEmail] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createAutoPassword, setCreateAutoPassword] = useState(false)
  const [createRoles, setCreateRoles] = useState({ cashier: false, manager: false, owner: false })
  const [createActive, setCreateActive] = useState(true)
  const [creatingUser, setCreatingUser] = useState(false)

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
    } catch (error) {
      handleApiError(error)
    } finally {
      setUserBusy(user.id, false)
    }
  }

  const toggleRole = async (user: User, roleName: 'cashier' | 'manager') => {
    const roleNames = user.roles.map((role) => role.name)
    const nextRoles = roleNames.includes(roleName)
      ? roleNames.filter((role) => role !== roleName)
      : [...roleNames, roleName]
    await updateRoles(user, nextRoles)
  }

  const handlePasswordChange = async (user: User) => {
    const password = passwords[user.id] ?? ''
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
      setPasswords((prev) => ({ ...prev, [user.id]: '' }))
      addToast(t('adminUsers.passwordUpdated'), 'success')
    } catch (error) {
      handleApiError(error)
    } finally {
      setUserBusy(user.id, false)
    }
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h2 className="page-title">{t('adminNav.users')}</h2>
            <p className="page-subtitle">{t('adminUsers.subtitle')}</p>
          </div>
          <button type="button" onClick={openCreateModal}>
            {t('adminUsers.createUser', { defaultValue: 'Создать пользователя' })}
          </button>
        </div>
      </div>
      <section className="card">
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
                  const hasCashier = roleNames.includes('cashier')
                  const hasManager = roleNames.includes('manager')
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
                              <span key={role} className="badge badge--role">
                                {role}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td>{user.is_active ? t('common.yes') : t('common.no')}</td>
                      <td>
                        <div className="form-stack">
                          <div className="role-toggle">
                            <span className="role-toggle__label">
                              {t('adminUsers.roles', { defaultValue: 'Роли' })}
                            </span>
                            <button
                              type="button"
                              className={`secondary role-toggle__button${hasCashier ? ' role-toggle__button--active' : ''}`}
                              onClick={() => toggleRole(user, 'cashier')}
                              disabled={isBusy || hasOwner}
                            >
                              cashier
                            </button>
                            <button
                              type="button"
                              className={`secondary role-toggle__button${hasManager ? ' role-toggle__button--active' : ''}`}
                              onClick={() => toggleRole(user, 'manager')}
                              disabled={isBusy || hasOwner}
                            >
                              manager
                            </button>
                            {hasOwner && (
                              <span className="muted role-toggle__hint">
                                {t('adminUsers.ownerLocked', { defaultValue: 'Owner роли нельзя менять' })}
                              </span>
                            )}
                          </div>
                          <div className="form-inline">
                            <input
                              type="password"
                              placeholder={t('adminUsers.newPasswordPlaceholder')}
                              value={passwords[user.id] ?? ''}
                              onChange={(event) =>
                                setPasswords((prev) => ({ ...prev, [user.id]: event.target.value }))
                              }
                            />
                            <button type="button" onClick={() => handlePasswordChange(user)} disabled={isBusy}>
                              {t('adminUsers.setPassword')}
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {createOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('adminUsers.createUser', { defaultValue: 'Создать пользователя' })}</h4>
              <button className="ghost" onClick={closeCreateModal} disabled={creatingUser}>
                {t('common.cancel')}
              </button>
            </div>
            <form className="form-stack" onSubmit={handleCreateSubmit}>
              <input
                type="email"
                placeholder={t('common.email')}
                value={createEmail}
                onChange={(event) => setCreateEmail(event.target.value)}
                required
              />
              <div className="form-stack">
                <div className="form-inline">
                  <input
                    type="password"
                    placeholder={t('adminUsers.newPasswordPlaceholder')}
                    value={createPassword}
                    onChange={(event) => {
                      setCreatePassword(event.target.value)
                      setCreateAutoPassword(false)
                    }}
                    disabled={createAutoPassword}
                  />
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      const generated = generatePassword()
                      setCreatePassword(generated)
                      setCreateAutoPassword(true)
                    }}
                  >
                    {t('adminUsers.generatePassword', { defaultValue: 'Сгенерировать' })}
                  </button>
                </div>
                <label className="form-inline">
                  <input
                    type="checkbox"
                    checked={createAutoPassword}
                    onChange={(event) => {
                      const nextValue = event.target.checked
                      setCreateAutoPassword(nextValue)
                      if (nextValue && !createPassword) {
                        setCreatePassword(generatePassword())
                      }
                    }}
                  />
                  <span>{t('adminUsers.autoPassword', { defaultValue: 'Автогенерация пароля' })}</span>
                </label>
              </div>
              <div className="form-stack">
                <span className="muted">{t('adminUsers.roles')}</span>
                <label className="form-inline">
                  <input
                    type="checkbox"
                    checked={createRoles.cashier}
                    onChange={(event) =>
                      setCreateRoles((prev) => ({ ...prev, cashier: event.target.checked }))
                    }
                  />
                  <span>cashier</span>
                </label>
                <label className="form-inline">
                  <input
                    type="checkbox"
                    checked={createRoles.manager}
                    onChange={(event) =>
                      setCreateRoles((prev) => ({ ...prev, manager: event.target.checked }))
                    }
                  />
                  <span>manager</span>
                </label>
                <label className="form-inline">
                  <input type="checkbox" checked={createRoles.owner} disabled />
                  <span>owner</span>
                </label>
              </div>
              <label className="form-inline">
                <input
                  type="checkbox"
                  checked={createActive}
                  onChange={(event) => setCreateActive(event.target.checked)}
                />
                <span>{t('adminUsers.active')}</span>
              </label>
              <div className="form-row">
                <button type="submit" disabled={creatingUser}>
                  {t('common.save', { defaultValue: 'Сохранить' })}
                </button>
                <button type="button" className="ghost" onClick={closeCreateModal} disabled={creatingUser}>
                  {t('common.cancel')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
