import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useTenantSettings } from '../../api/tenantSettings'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'
import PageTitle from '../../components/PageTitle'

type Product = {
  id: string
  name: string
  variant_group?: string | null
  variant_name?: string | null
  is_hidden: boolean
}

export default function AdminCatalogVisibilityPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const { data: tenantSettings } = useTenantSettings()
  const [items, setItems] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const catalogPublicUrl = `${window.location.origin}/catalog`

  const isPublicCatalogModuleEnabled = useMemo(() => {
    if (!tenantSettings) return false
    const module = tenantSettings.modules.find((item) => item.code === 'public_catalog')
    return Boolean(module?.is_active && module?.is_enabled)
  }, [tenantSettings])

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get<Product[]>('/products', { params: { is_active: true } })
      setItems(res.data)
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!isPublicCatalogModuleEnabled) {
      setItems([])
      setLoading(false)
      return
    }
    void load()
  }, [isPublicCatalogModuleEnabled])

  const toggle = async (item: Product) => {
    try {
      await api.patch(`/products/${item.id}`, { is_hidden: !item.is_hidden })
      await load()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  return (
    <div className="page">
      <PageTitle title={t('adminNav.catalogVisibility')} subtitle={t('adminCatalogVisibility.subtitle')} />
      <p className="page-subtitle">
        {t('adminCatalogVisibility.publicUrl')}: <a href={catalogPublicUrl}>{catalogPublicUrl}</a>
      </p>
      {!isPublicCatalogModuleEnabled ? (
        <p className="page-subtitle">{t('adminCatalogVisibility.moduleDisabled')}</p>
      ) : (
        <table className={loading ? 'table table--skeleton' : 'table'}>
          <thead>
            <tr>
              <th>{t('admin.table.name')}</th>
              <th>{t('adminCatalogVisibility.variant')}</th>
              <th>{t('adminCatalogVisibility.hidden')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.variant_group || item.name}</td>
                <td>{item.variant_name || '-'}</td>
                <td>
                  <input type="checkbox" checked={item.is_hidden} onChange={() => toggle(item)} />
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={3}>{t('adminCatalogVisibility.empty')}</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
