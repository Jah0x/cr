import type { CSSProperties } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { useTenantSettings } from '../api/tenantSettings'

const adminModules = ['catalog', 'purchasing', 'stock', 'sales', 'reports', 'users', 'finance']

export default function TenantLayout() {
  const location = useLocation()
  const { data, isLoading } = useTenantSettings()

  const isModuleEnabled = (code: string) => {
    if (!data) return true
    const module = data.modules.find((item) => item.code === code)
    return module ? module.is_active && module.is_enabled : true
  }

  const showAdmin = isLoading || adminModules.some((code) => isModuleEnabled(code))
  const showPos = isLoading || isModuleEnabled('pos')
  const showFinance = isLoading || isModuleEnabled('finance')

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

  return (
    <div>
      <nav style={navStyle}>
        <span style={{ fontWeight: 700 }}>Tenant Console</span>
        {showAdmin && <Link style={linkStyle('/admin')} to="/admin">Admin</Link>}
        {showPos && <Link style={linkStyle('/pos')} to="/pos">POS</Link>}
        {showFinance && <Link style={linkStyle('/finance')} to="/finance">Finance</Link>}
        <Link style={linkStyle('/settings')} to="/settings">Settings</Link>
      </nav>
      <Outlet />
    </div>
  )
}
