import type { CSSProperties } from 'react'
import { useEffect, useState } from 'react'
import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useTenantSettings } from '../api/tenantSettings'
import api from '../api/client'

const adminModules = ['catalog', 'purchasing', 'stock', 'sales', 'reports', 'users', 'finance']

export default function TenantLayout() {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const { data, isLoading } = useTenantSettings()
  const [isAuthValid, setIsAuthValid] = useState(true)
  const token = localStorage.getItem('token')
  const storedUserRaw = localStorage.getItem('user')

  let isCashierOrOwner = false
  try {
    const parsedUser = storedUserRaw ? (JSON.parse(storedUserRaw) as { roles?: Array<{ name?: string }> }) : null
    isCashierOrOwner =
      parsedUser?.roles?.some((role) => role.name === 'cashier' || role.name === 'owner') ?? false
  } catch {
    isCashierOrOwner = false
  }

  useEffect(() => {
    if (!token) return

    let isActive = true

    api
      .get('/auth/me')
      .catch((error) => {
        if (!isActive) return
        if (error?.response?.status === 401) {
          localStorage.removeItem('token')
          setIsAuthValid(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [token])

  const isModuleEnabled = (code: string) => {
    if (!data) return true
    const module = data.modules.find((item) => item.code === code)
    return module ? module.is_active && module.is_enabled : true
  }

  const showAdmin = isLoading || adminModules.some((code) => isModuleEnabled(code))
  const showPos = isLoading || isModuleEnabled('pos')
  const showFinance = isLoading || isModuleEnabled('finance')
  const showShifts = (isLoading || isModuleEnabled('sales')) && isCashierOrOwner

  const compactNav = data?.ui_prefs?.compact_nav ?? false

  const navStyle: CSSProperties = {
    display: 'flex',
    gap: 12,
    padding: compactNav ? '8px 16px' : '16px 24px',
    background: '#0f172a',
    color: '#fff',
    alignItems: 'center'
  }

  const linkStyle = (path: string): CSSProperties => ({
    color: location.pathname === path ? '#38bdf8' : '#fff',
    textDecoration: 'none',
    fontWeight: 600
  })

  if (!token || !isAuthValid) {
    return <Navigate to="/login" replace />
  }

  return (
    <div>
      <nav style={navStyle}>
        <span style={{ fontWeight: 700 }}>{t('nav.tenantConsole')}</span>
        {showAdmin && (
          <Link style={linkStyle('/admin')} to="/admin">
            {t('nav.admin')}
          </Link>
        )}
        {showPos && (
          <Link style={linkStyle('/pos')} to="/pos">
            {t('nav.pos')}
          </Link>
        )}
        {showFinance && (
          <Link style={linkStyle('/finance')} to="/finance">
            {t('nav.finance')}
          </Link>
        )}
        {showShifts && (
          <Link style={linkStyle('/shifts')} to="/shifts">
            {t('nav.shifts')}
          </Link>
        )}
        <Link style={linkStyle('/settings')} to="/settings">
          {t('nav.settings')}
        </Link>
        <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12 }}>{t('language.label')}</span>
          <select
            value={i18n.language}
            onChange={(event) => i18n.changeLanguage(event.target.value)}
          >
            <option value="ru">{t('language.ru')}</option>
            <option value="en">{t('language.en')}</option>
          </select>
        </label>
      </nav>
      <Outlet />
    </div>
  )
}
