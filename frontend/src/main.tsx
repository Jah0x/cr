import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './styles/global.css'
import LoginPage from './pages/LoginPage'
import AdminDashboard from './pages/AdminDashboard'
import PosPage from './pages/PosPage'
import TenantLayout from './components/TenantLayout'
import PlatformLayout from './components/PlatformLayout'
import PlatformLoginPage from './pages/PlatformLoginPage'
import PlatformTenantsPage from './pages/PlatformTenantsPage'
import PlatformTenantCreatePage from './pages/PlatformTenantCreatePage'
import TenantSettingsPage from './pages/TenantSettingsPage'

const queryClient = new QueryClient()
const platformHosts = (import.meta.env.VITE_PLATFORM_HOSTS ?? '')
  .split(',')
  .map((host: string) => host.trim().toLowerCase())
  .filter(Boolean)
const currentHost = window.location.hostname.toLowerCase()
const isPlatformHost = platformHosts.includes(currentHost) || currentHost.startsWith('platform.')
const hostMode: 'platform' | 'tenant' = isPlatformHost ? 'platform' : 'tenant'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {hostMode === 'platform' ? (
          <Routes>
            <Route path="/platform/login" element={<PlatformLoginPage />} />
            <Route element={<PlatformLayout />}>
              <Route path="/platform/tenants" element={<PlatformTenantsPage />} />
              <Route path="/platform/tenants/new" element={<PlatformTenantCreatePage />} />
            </Route>
            <Route path="*" element={<Navigate to="/platform/login" />} />
          </Routes>
        ) : (
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<TenantLayout />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/pos" element={<PosPage />} />
              <Route path="/settings" element={<TenantSettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        )}
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
