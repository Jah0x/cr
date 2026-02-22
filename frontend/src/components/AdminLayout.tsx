import { useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const adminRoutes = [
  { key: 'catalog', path: '/admin/catalog' },
  { key: 'purchasing', path: '/admin/purchasing' },
  { key: 'stock', path: '/admin/stock' },
  { key: 'reports', path: '/admin/reports' },
  { key: 'users', path: '/admin/users' },
  { key: 'catalogVisibility', path: '/admin/catalog-visibility' }
]

export default function AdminLayout() {
  const { t } = useTranslation()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const pageTitle = useMemo(() => {
    const match = adminRoutes.find((route) => location.pathname.startsWith(route.path))
    if (!match) {
      return t('admin.title')
    }
    return t(`adminNav.${match.key}`)
  }, [location.pathname, t])

  return (
    <div className="admin-shell">
      <aside className={`admin-side ${menuOpen ? 'admin-side--open' : ''}`}>
        <div className="admin-side__brand">{t('admin.title')}</div>
        <nav className="admin-nav">
          {adminRoutes.map((route) => (
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
