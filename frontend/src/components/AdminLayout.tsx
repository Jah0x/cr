import { useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useTenantSettings } from '../api/tenantSettings'

type AdminRoute = {
  key: string
  path: string
  moduleCode?: string
}

const adminRoutes: AdminRoute[] = [
  { key: 'catalog', path: '/admin/catalog', moduleCode: 'catalog' },
  { key: 'purchasing', path: '/admin/purchasing', moduleCode: 'purchasing' },
  { key: 'stock', path: '/admin/stock', moduleCode: 'stock' },
  { key: 'reports', path: '/admin/reports', moduleCode: 'reports' },
  { key: 'users', path: '/admin/users', moduleCode: 'users' },
  { key: 'catalogVisibility', path: '/admin/catalog-visibility', moduleCode: 'public_catalog' }
]

export default function AdminLayout() {
  const { t } = useTranslation()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const { data } = useTenantSettings()

  const isModuleEnabled = (code?: string) => {
    if (!code || !data) return true
    const module = data.modules.find((item) => item.code === code)
    return module ? module.is_active && module.is_enabled : false
  }

  const visibleRoutes = adminRoutes.filter((route) => isModuleEnabled(route.moduleCode))

  const pageTitle = useMemo(() => {
    const match = visibleRoutes.find((route) => location.pathname.startsWith(route.path))
    if (!match) {
      return t('admin.title')
    }
    return t(`adminNav.${match.key}`)
  }, [location.pathname, t, visibleRoutes])

  return (
    <div className="admin-shell">
      <aside className={`admin-side ${menuOpen ? 'admin-side--open' : ''}`}>
        <div className="admin-side__brand">{t('admin.title')}</div>
        <nav className="admin-nav">
          {visibleRoutes.map((route) => (
            <NavLink
              key={route.key}
              to={route.path}
              onClick={() => setMenuOpen(false)}
            >
              {t(`adminNav.${route.key}`)}
            </NavLink>
          ))}
        </nav>
      </aside>
      {menuOpen && (
        <button
          className="admin-side__backdrop"
          type="button"
          aria-label={t('admin.menuClose')}
          onClick={() => setMenuOpen(false)}
        />
      )}
      <main className="admin-main">
        <div className="admin-main__header">
          <button
            className="admin-menu-toggle ghost"
            type="button"
            aria-label={t('admin.menuToggle')}
            onClick={() => setMenuOpen(true)}
          >
            ☰
          </button>
          <h1>{pageTitle}</h1>
        </div>
        <div className="admin-main__content">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
