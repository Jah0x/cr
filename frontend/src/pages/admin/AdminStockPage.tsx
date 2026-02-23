import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'
import { PrimaryButton } from '../../components/Buttons'
import PageTitle from '../../components/PageTitle'

type Product = { id: string; name: string }

type StockLevel = { product_id: string; on_hand: number }

type StockMove = {
  id: string
  product_id: string
  quantity: number
  delta_qty: number
  reason: string
  created_at: string
}

type AdjustmentMode = 'set' | 'increase' | 'decrease'

type FastApiValidationError = { loc?: Array<string | number>; msg: string; type?: string }

type ApiErrorPayload = { detail?: string | FastApiValidationError[]; message?: string }

type StockTab = 'levels' | 'adjustments'

export default function AdminStockPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState<StockTab>('levels')
  const [products, setProducts] = useState<Product[]>([])
  const [stockLevels, setStockLevels] = useState<StockLevel[]>([])
  const [productsLoading, setProductsLoading] = useState(true)
  const [stockLevelsLoading, setStockLevelsLoading] = useState(true)
  const [stockMoves, setStockMoves] = useState<StockMove[]>([])
  const [stockMovesLoading, setStockMovesLoading] = useState(true)
  const [stockProduct, setStockProduct] = useState('')
  const [stockQty, setStockQty] = useState('0')
  const [stockReason, setStockReason] = useState('')
  const [adjustmentMode, setAdjustmentMode] = useState<AdjustmentMode>('set')
  const [adjustModalOpen, setAdjustModalOpen] = useState(false)

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
    setProductsLoading(true)
    try {
      const res = await api.get('/products')
      setProducts(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setProductsLoading(false)
    }
  }

  const loadStockLevels = async () => {
    setStockLevelsLoading(true)
    try {
      const res = await api.get('/stock')
      setStockLevels(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setStockLevelsLoading(false)
    }
  }

  const loadStockMoves = async () => {
    setStockMovesLoading(true)
    try {
      const res = await api.get('/stock/moves')
      setStockMoves(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setStockMovesLoading(false)
    }
  }

  useEffect(() => {
    void loadProducts()
    void loadStockLevels()
    void loadStockMoves()
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
    const qty = Number(stockQty)
    const currentQty = Number(stockLevels.find((item) => item.product_id === stockProduct)?.on_hand ?? 0)
    const deltaQty =
      adjustmentMode === 'set' ? qty - currentQty : adjustmentMode === 'increase' ? qty : qty * -1
    if (adjustmentMode !== 'set' && qty <= 0) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    if (adjustmentMode === 'decrease' && qty > currentQty) {
      addToast(t('adminStock.decreaseLimitError'), 'error')
      return
    }
    try {
      await api.post('/stock/adjustments', {
        product_id: stockProduct,
        quantity: deltaQty,
        reason: stockReason.trim() || t('adminStock.defaultReason')
      })
      addToast(t('common.updated'), 'success')
      setStockQty('0')
      setStockReason('')
      loadStockLevels()
      loadStockMoves()
      setAdjustModalOpen(false)
    } catch (error) {
      handleApiError(error)
    }
  }

  const openAdjustModal = () => {
    setAdjustModalOpen(true)
  }

  const closeAdjustModal = () => {
    setAdjustModalOpen(false)
  }

  const selectedOnHand = Number(stockLevels.find((item) => item.product_id === stockProduct)?.on_hand ?? 0)
  const enteredQty = Number(stockQty)
  const stockPreview = Number.isFinite(enteredQty)
    ? adjustmentMode === 'set'
      ? enteredQty
      : adjustmentMode === 'increase'
        ? selectedOnHand + enteredQty
        : selectedOnHand - enteredQty
    : selectedOnHand

  const renderSkeletonRows = (rows: number, columns: number) =>
    Array.from({ length: rows }, (_, rowIndex) => (
      <tr key={`skeleton-${rowIndex}`}>
        {Array.from({ length: columns }, (_, columnIndex) => (
          <td key={`skeleton-${rowIndex}-${columnIndex}`}>
            <span className="skeleton skeleton-text" />
          </td>
        ))}
      </tr>
    ))

  return (
    <div className="admin-page">
      <PageTitle
        title={t('adminNav.stock')}
        subtitle={t('adminStock.subtitle')}
        actions={
          <PrimaryButton type="button" onClick={openAdjustModal}>
            {t('common.add', { defaultValue: 'Добавить' })}
          </PrimaryButton>
        }
      />
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
            <table className={stockLevelsLoading ? 'table table--skeleton' : 'table'}>
              <thead>
                <tr>
                  <th scope="col">{t('admin.table.name')}</th>
                  <th scope="col">{t('adminStock.onHand')}</th>
                </tr>
              </thead>
              <tbody>
                {stockLevelsLoading ? (
                  renderSkeletonRows(4, 2)
                ) : stockLevels.length === 0 ? (
                  <tr>
                    <td colSpan={2}>
                      <div className="form-stack">
                        <span className="page-subtitle">{t('adminStock.emptyLevels')}</span>
                        <PrimaryButton type="button" onClick={openAdjustModal}>
                          {t('common.add', { defaultValue: 'Добавить' })}
                        </PrimaryButton>
                      </div>
                    </td>
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
          <div className="table-wrapper">
            <table className={stockMovesLoading ? 'table table--skeleton' : 'table'}>
              <thead>
                <tr>
                  <th scope="col">{t('admin.table.name')}</th>
                  <th scope="col">{t('adminStock.delta')}</th>
                  <th scope="col">{t('adminStock.reason')}</th>
                </tr>
              </thead>
              <tbody>
                {stockMovesLoading ? (
                  renderSkeletonRows(4, 3)
                ) : stockMoves.length ? (
                  stockMoves
                    .slice()
                    .reverse()
                    .map((item) => (
                      <tr key={item.id}>
                        <td>{productMap.get(item.product_id) ?? '—'}</td>
                        <td>{Number(item.delta_qty) > 0 ? `+${item.delta_qty}` : item.delta_qty}</td>
                        <td>{item.reason || '—'}</td>
                      </tr>
                    ))
                ) : (
                  <tr>
                    <td colSpan={3}>{t('adminStock.emptyAdjustments')}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {adjustModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('adminStock.adjustmentsTitle')}</h4>
              <button className="ghost" onClick={closeAdjustModal}>
                {t('common.close')}
              </button>
            </div>
            <div className="form-stack">
              <p className="page-subtitle">{t('adminStock.adjustmentsSubtitle')}</p>
              <div className="form-row">
                <label className="form-field">
                  <span>{t('adminStock.productField')}</span>
                  <select
                    value={stockProduct}
                    onChange={(e) => setStockProduct(e.target.value)}
                    disabled={productsLoading}
                  >
                    <option value="">{t('adminStock.productPlaceholder')}</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>{t('adminStock.modeField')}</span>
                  <select
                    value={adjustmentMode}
                    onChange={(e) => setAdjustmentMode(e.target.value as AdjustmentMode)}
                  >
                    <option value="set">{t('adminStock.modeSet')}</option>
                    <option value="increase">{t('adminStock.modeIncrease')}</option>
                    <option value="decrease">{t('adminStock.modeDecrease')}</option>
                  </select>
                </label>
                <label className="form-field">
                  <span>{t('adminStock.qtyField')}</span>
                  <input
                    type="number"
                    min="0"
                    placeholder={t('adminStock.qtyPlaceholderDetailed')}
                    value={stockQty}
                    onChange={(e) => setStockQty(e.target.value)}
                  />
                </label>
              </div>
              <div className="form-row">
                <label className="form-field">
                  <span>{t('adminStock.reasonField')}</span>
                  <input
                    placeholder={t('adminStock.reasonPlaceholder')}
                    value={stockReason}
                    onChange={(e) => setStockReason(e.target.value)}
                  />
                </label>
                <div className="form-field">
                  <span>{t('adminStock.currentAndNext')}</span>
                  <div className="page-subtitle">
                    {t('adminStock.previewText', { current: selectedOnHand, next: stockPreview })}
                  </div>
                </div>
                <button onClick={adjustStock}>{t('admin.adjust')}</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
