import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'

type Product = { id: string; name: string }

type StockLevel = { product_id: string; on_hand: number }

type FastApiValidationError = { loc?: Array<string | number>; msg: string; type?: string }

type ApiErrorPayload = { detail?: string | FastApiValidationError[]; message?: string }

type StockTab = 'levels' | 'adjustments'

export default function AdminStockPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState<StockTab>('levels')
  const [products, setProducts] = useState<Product[]>([])
  const [stockLevels, setStockLevels] = useState<StockLevel[]>([])
  const [stockProduct, setStockProduct] = useState('')
  const [stockQty, setStockQty] = useState('0')

  const productMap = useMemo(() => new Map(products.map((item) => [item.id, item.name])), [products])

  const formatValidationErrors = (errors: FastApiValidationError[]) =>
    errors
      .map((item) => {
        if (item.loc?.length) {
          return `${item.loc.join('.')}: ${item.msg}`
        }
        return item.msg
      })
      .join(', ')

  const handleApiError = (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const status = error.response?.status
      if (status === 409) {
        addToast(t('admin.errors.alreadyExists'), 'error')
        return
      }
      if (status === 422) {
        const data = error.response?.data as ApiErrorPayload | undefined
        const detail = data?.detail ?? data?.message
        if (Array.isArray(detail)) {
          const message = formatValidationErrors(detail)
          addToast(message || t('common.error'), 'error')
          return
        }
        addToast(detail || t('common.error'), 'error')
        return
      }
      if (status === 500) {
        const data = error.response?.data as ApiErrorPayload | undefined
        const detail = data?.detail ?? data?.message
        if (typeof detail === 'string') {
          addToast(detail || t('common.error'), 'error')
          return
        }
        if (detail) {
          const safeDetail = typeof detail === 'object' ? JSON.stringify(detail) : String(detail)
          addToast(`Internal error: ${safeDetail}`, 'error')
          return
        }
        addToast(t('common.error'), 'error')
        return
      }
    }
    addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  }

  const loadProducts = async () => {
    try {
      const res = await api.get('/products')
      setProducts(res.data)
    } catch (error) {
      handleApiError(error)
    }
  }

  const loadStockLevels = async () => {
    try {
      const res = await api.get('/stock')
      setStockLevels(res.data)
    } catch (error) {
      handleApiError(error)
    }
  }

  useEffect(() => {
    void loadProducts()
    void loadStockLevels()
  }, [])

  const isNonNegativeNumber = (value: string) => {
    const parsed = Number(value)
    return Number.isFinite(parsed) && parsed >= 0
  }

  const adjustStock = async () => {
    if (!stockProduct || !isNonNegativeNumber(stockQty)) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post('/stock/adjustments', {
        product_id: stockProduct,
        quantity: Number(stockQty),
        reason: 'adjustment'
      })
      addToast(t('common.updated'), 'success')
      setStockQty('0')
      loadStockLevels()
    } catch (error) {
      handleApiError(error)
    }
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h2 className="page-title">{t('adminNav.stock')}</h2>
        <p className="page-subtitle">{t('adminStock.subtitle')}</p>
      </div>
      <div className="tabs">
        <button
          type="button"
          className={activeTab === 'levels' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('levels')}
        >
          {t('adminTabs.stockLevels')}
        </button>
        <button
          type="button"
          className={activeTab === 'adjustments' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('adjustments')}
        >
          {t('adminTabs.adjustments')}
        </button>
      </div>

      {activeTab === 'levels' && (
        <section className="card">
          <h3>{t('adminStock.levelsTitle')}</h3>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">{t('admin.table.name')}</th>
                  <th scope="col">{t('adminStock.onHand')}</th>
                </tr>
              </thead>
              <tbody>
                {stockLevels.length === 0 ? (
                  <tr>
                    <td colSpan={2}>{t('adminStock.emptyLevels')}</td>
                  </tr>
                ) : (
                  stockLevels.map((item) => (
                    <tr key={item.product_id}>
                      <td>{productMap.get(item.product_id) ?? '—'}</td>
                      <td>{item.on_hand}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === 'adjustments' && (
        <section className="card">
          <div>
            <h3>{t('adminStock.adjustmentsTitle')}</h3>
            <p className="page-subtitle">{t('adminStock.adjustmentsSubtitle')}</p>
          </div>
          <div className="form-row">
            <select value={stockProduct} onChange={(e) => setStockProduct(e.target.value)}>
              <option value="">{t('admin.productSelect')}</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
            <input
              type="number"
              min="0"
              placeholder={t('admin.qtyPlaceholder')}
              value={stockQty}
              onChange={(e) => setStockQty(e.target.value)}
            />
            <button onClick={adjustStock}>{t('admin.adjust')}</button>
          </div>
        </section>
      )}
    </div>
  )
}
