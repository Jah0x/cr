import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './styles/global.css'
import './i18n'
import LoginPage from './pages/LoginPage'
import AdminLayout from './components/AdminLayout'
import AdminCatalogPage from './pages/admin/AdminCatalogPage'
import AdminPurchasingPage from './pages/admin/AdminPurchasingPage'
import AdminStockPage from './pages/admin/AdminStockPage'
import AdminReportsPage from './pages/admin/AdminReportsPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import PosPage from './pages/PosPage'
import TenantLayout from './components/TenantLayout'
import PlatformLayout from './components/PlatformLayout'
import PlatformLoginPage from './pages/PlatformLoginPage'
import PlatformTenantsPage from './pages/PlatformTenantsPage'
import PlatformTenantCreatePage from './pages/PlatformTenantCreatePage'
import TenantSettingsPage from './pages/TenantSettingsPage'
import FinancePage from './pages/FinancePage'
import ShiftsPage from './pages/ShiftsPage'
import RegisterPage from './pages/RegisterPage'
import { loadRuntimeConfig } from './config/runtimeConfig'
import { ToastProvider } from './components/ToastProvider'

const queryClient = new QueryClient()
const platformHostsFromEnv = (import.meta.env.VITE_PLATFORM_HOSTS ?? '')
  .split(',')
  .map((host: string) => host.trim().toLowerCase())
  .filter(Boolean)

const bootstrap = async () => {
  const runtimeConfig = await loadRuntimeConfig()
  const runtimePlatformHosts = runtimeConfig?.platformHosts
  const platformHosts =
    runtimePlatformHosts && runtimePlatformHosts.length > 0 ? runtimePlatformHosts : platformHostsFromEnv
  const currentHost = window.location.hostname.toLowerCase()
  const isPlatformHost = platformHosts.includes(currentHost)
  const hostMode: 'platform' | 'tenant' = isPlatformHost ? 'platform' : 'tenant'

  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
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
                <Route path="/invite/:token" element={<RegisterPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route element={<TenantLayout />}>
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route index element={<Navigate to="catalog" replace />} />
                    <Route path="catalog" element={<AdminCatalogPage />} />
                    <Route path="purchasing" element={<AdminPurchasingPage />} />
                    <Route path="stock" element={<AdminStockPage />} />
                    <Route path="reports" element={<AdminReportsPage />} />
                    <Route path="users" element={<AdminUsersPage />} />
                  </Route>
                  <Route path="/pos" element={<PosPage />} />
                  <Route path="/finance" element={<FinancePage />} />
                  <Route path="/shifts" element={<ShiftsPage />} />
                  <Route path="/settings" element={<TenantSettingsPage />} />
                </Route>
                <Route path="*" element={<Navigate to="/login" />} />
              </Routes>
            )}
          </BrowserRouter>
        </ToastProvider>
      </QueryClientProvider>
    </React.StrictMode>
  )
}

void bootstrap()
