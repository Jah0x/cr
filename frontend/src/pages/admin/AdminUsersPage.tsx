import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'

type Role = { id: string; name: string }

type User = { id: string; email: string; is_active: boolean; roles: Role[] }

export default function AdminUsersPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [busyUsers, setBusyUsers] = useState<Record<string, boolean>>({})
  const [passwords, setPasswords] = useState<Record<string, string>>({})

  const setUserBusy = (userId: string, isBusy: boolean) => {
    setBusyUsers((prev) => ({ ...prev, [userId]: isBusy }))
  }

  const updateUserState = (updated: User) => {
    setUsers((prev) => prev.map((user) => (user.id === updated.id ? updated : user)))
  }

  const handleApiError = (error: unknown) => {
    addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
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

  const assignCashier = async (user: User) => {
    const roleNames = user.roles.map((role) => role.name)
    if (!roleNames.includes('cashier')) {
      roleNames.push('cashier')
    }
    await updateRoles(user, roleNames)
  }

  const removeCashier = async (user: User) => {
    const roleNames = user.roles.map((role) => role.name).filter((role) => role !== 'cashier')
    await updateRoles(user, roleNames)
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
        <h2 className="page-title">{t('adminNav.users')}</h2>
        <p className="page-subtitle">{t('adminUsers.subtitle')}</p>
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
                  const hasCashier = roleNames.includes('cashier')
                  const isBusy = Boolean(busyUsers[user.id])
                  return (
                    <tr key={user.id}>
                      <td>{user.email}</td>
                      <td>
                        {roleNames.length === 0 ? (
                          <span className="muted">{t('adminUsers.noRoles')}</span>
                        ) : (
                          <div className="form-inline">
                            {roleNames.map((role) => (
                              <span key={role} className="pill">
                                {role}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td>{user.is_active ? t('common.yes') : t('common.no')}</td>
                      <td>
                        <div className="form-stack">
                          <div className="form-inline">
                            {hasCashier ? (
                              <button type="button" onClick={() => removeCashier(user)} disabled={isBusy}>
                                {t('adminUsers.removeCashier')}
                              </button>
                            ) : (
                              <button type="button" onClick={() => assignCashier(user)} disabled={isBusy}>
                                {t('adminUsers.assignCashier')}
                              </button>
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
    </div>
  )
}
