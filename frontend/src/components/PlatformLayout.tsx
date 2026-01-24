import type { CSSProperties } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

export default function PlatformLayout() {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/platform/login')
    }
  }, [navigate])

  const linkStyle = (path: string): CSSProperties => ({
    color: location.pathname === path ? '#38bdf8' : '#fff',
    textDecoration: 'none',
    fontWeight: 600
  })

  return (
    <div>
      <nav style={{ display: 'flex', gap: 12, padding: '16px 24px', background: '#111827', color: '#fff' }}>
        <span style={{ fontWeight: 700 }}>{t('nav.platform')}</span>
        <Link style={linkStyle('/platform/tenants')} to="/platform/tenants">
          {t('nav.tenants')}
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
