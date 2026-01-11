import type { CSSProperties } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

export default function PlatformLayout() {
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
        <span style={{ fontWeight: 700 }}>Platform</span>
        <Link style={linkStyle('/platform/tenants')} to="/platform/tenants">Tenants</Link>
      </nav>
      <Outlet />
    </div>
  )
}
