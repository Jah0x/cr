import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'
import { PrimaryButton } from '../../components/Buttons'
import PageTitle from '../../components/PageTitle'

type Supplier = { id: string; name: string }

type Product = { id: string; name: string }

type PurchaseInvoice = { id: string; status: string; supplier_id?: string | null }

type PurchaseItem = {
  id: string
  product_id: string
  quantity: number
  unit_cost: number
}

type PurchaseInvoiceDetail = PurchaseInvoice & { items: PurchaseItem[] }

type FastApiValidationError = { loc?: Array<string | number>; msg: string; type?: string }

type ApiErrorPayload = { detail?: string | FastApiValidationError[]; message?: string }

type PurchasingTab = 'suppliers' | 'invoices'

export default function AdminPurchasingPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState<PurchasingTab>('suppliers')
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [invoices, setInvoices] = useState<PurchaseInvoice[]>([])
  const [suppliersLoading, setSuppliersLoading] = useState(true)
  const [productsLoading, setProductsLoading] = useState(true)
  const [invoicesLoading, setInvoicesLoading] = useState(true)
  const [invoiceDetailLoading, setInvoiceDetailLoading] = useState(false)
  const [supplierName, setSupplierName] = useState('')
  const [invoiceSupplierId, setInvoiceSupplierId] = useState('')
  const [invoiceId, setInvoiceId] = useState('')
  const [invoiceDetail, setInvoiceDetail] = useState<PurchaseInvoiceDetail | null>(null)
  const [purchaseProduct, setPurchaseProduct] = useState('')
  const [purchaseQty, setPurchaseQty] = useState('0')
  const [purchaseCost, setPurchaseCost] = useState('0')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createModalTab, setCreateModalTab] = useState<PurchasingTab>('suppliers')

  const productMap = useMemo(() => new Map(products.map((item) => [item.id, item.name])), [products])
  const supplierMap = useMemo(() => new Map(suppliers.map((item) => [item.id, item.name])), [suppliers])

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

  const confirmDeletion = () =>
    window.confirm(
      t('common.confirmDelete', { defaultValue: 'Are you sure you want to delete this item?' })
    )

  const loadSuppliers = async () => {
    setSuppliersLoading(true)
    try {
      const res = await api.get('/suppliers')
      setSuppliers(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setSuppliersLoading(false)
    }
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

  const loadInvoices = async () => {
    setInvoicesLoading(true)
    try {
      const res = await api.get('/purchase-invoices', { params: { status: 'draft' } })
      setInvoices(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setInvoicesLoading(false)
    }
  }

  useEffect(() => {
    void loadSuppliers()
    void loadProducts()
    void loadInvoices()
  }, [])

  useEffect(() => {
    if (!invoiceId) {
      setInvoiceDetail(null)
      return
    }
    const loadInvoiceDetail = async () => {
      setInvoiceDetailLoading(true)
      try {
        const res = await api.get(`/purchase-invoices/${invoiceId}`)
        setInvoiceDetail(res.data)
      } catch (error) {
        handleApiError(error)
      } finally {
        setInvoiceDetailLoading(false)
      }
    }
    void loadInvoiceDetail()
  }, [invoiceId])

  const createSupplier = async () => {
    if (!supplierName.trim()) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post('/suppliers', { name: supplierName.trim() })
      setSupplierName('')
      addToast(t('common.created'), 'success')
      loadSuppliers()
      setCreateModalOpen(false)
    } catch (error) {
      handleApiError(error)
    }
  }

  const deleteSupplier = async (supplierId: string) => {
    if (!confirmDeletion()) {
      return
    }
    try {
      await api.delete(`/suppliers/${supplierId}`)
      addToast(t('common.deleted'), 'success')
      loadSuppliers()
    } catch (error) {
      handleApiError(error)
    }
  }

  const createInvoice = async () => {
    if (!invoiceSupplierId) {
      addToast(t('adminPurchasing.selectSupplier'), 'error')
      return
    }
    try {
      const res = await api.post('/purchase-invoices', { supplier_id: invoiceSupplierId })
      setInvoiceId(res.data.id)
      addToast(t('common.created'), 'success')
      loadInvoices()
      setCreateModalOpen(false)
    } catch (error) {
      handleApiError(error)
    }
  }

  const addPurchaseItem = async () => {
    if (!invoiceId) return
    const qty = Number(purchaseQty)
    const cost = Number(purchaseCost)
    if (!purchaseProduct || !Number.isFinite(qty) || !Number.isFinite(cost)) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    if (qty < 0 || cost < 0) {
      addToast(t('admin.validation.nonNegative'), 'error')
      return
    }
    try {
      const res = await api.post(`/purchase-invoices/${invoiceId}/items`, {
        product_id: purchaseProduct,
        quantity: purchaseQty,
        unit_cost: purchaseCost
      })
      setPurchaseProduct('')
      setPurchaseQty('0')
      setPurchaseCost('0')
      setInvoiceDetail(res.data)
      addToast(t('common.created'), 'success')
      loadInvoices()
      setCreateModalOpen(false)
    } catch (error) {
      handleApiError(error)
    }
  }

  const postInvoice = async () => {
    if (!invoiceId) {
      addToast(t('adminPurchasing.selectInvoice'), 'error')
      return
    }
    try {
      await api.post(`/purchase-invoices/${invoiceId}/post`)
      addToast(t('common.updated'), 'success')
      setInvoiceId('')
      setInvoiceDetail(null)
      loadInvoices()
    } catch (error) {
      handleApiError(error)
    }
  }

  const openCreateModal = () => {
    setCreateModalTab(activeTab)
    setCreateModalOpen(true)
  }

  const closeCreateModal = () => {
    setCreateModalOpen(false)
  }

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
        title={t('adminNav.purchasing')}
        subtitle={t('adminPurchasing.subtitle')}
        actions={
          <PrimaryButton type="button" onClick={openCreateModal}>
            {t('common.add', { defaultValue: 'Добавить' })}
          </PrimaryButton>
        }
      />
      <div className="tabs">
        <button
          type="button"
          className={activeTab === 'suppliers' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('suppliers')}
        >
          {t('adminTabs.suppliers')}
        </button>
        <button
          type="button"
          className={activeTab === 'invoices' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('invoices')}
        >
          {t('adminTabs.invoices')}
        </button>
      </div>

      {activeTab === 'suppliers' && (
        <section className="card">
          <h3>{t('adminPurchasing.suppliersList')}</h3>
          <div className="table-wrapper">
            <table className={suppliersLoading ? 'table table--skeleton' : 'table'}>
              <thead>
                <tr>
                  <th scope="col">{t('admin.table.name')}</th>
                  <th scope="col">{t('admin.table.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {suppliersLoading ? (
                  renderSkeletonRows(4, 2)
                ) : suppliers.length === 0 ? (
                  <tr>
                    <td colSpan={2}>
                      <div className="form-stack">
                        <span className="page-subtitle">{t('adminPurchasing.emptySuppliers')}</span>
                        <PrimaryButton type="button" onClick={openCreateModal}>
                          {t('adminPurchasing.createSupplier')}
                        </PrimaryButton>
                      </div>
                    </td>
                  </tr>
                ) : (
                  suppliers.map((supplier) => (
                    <tr key={supplier.id}>
                      <td>{supplier.name}</td>
                      <td>
                        <button className="secondary" onClick={() => deleteSupplier(supplier.id)}>
                          {t('common.delete')}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === 'invoices' && (
        <div className="grid">
          <section className="card">
            <div>
              <h3>{t('adminPurchasing.workingInvoice')}</h3>
              <p className="page-subtitle">{t('adminPurchasing.workingInvoiceSubtitle')}</p>
            </div>
            <div className="form-row">
              <label className="form-field">
                <span>{t('adminPurchasing.selectInvoice')}</span>
                <select
                  value={invoiceId}
                  onChange={(e) => setInvoiceId(e.target.value)}
                  disabled={invoicesLoading}
                >
                  <option value="">{t('adminPurchasing.selectInvoicePlaceholder')}</option>
                  {invoices.map((invoice) => (
                    <option key={invoice.id} value={invoice.id}>
                      {invoice.id.slice(0, 8)} ·{' '}
                      {supplierMap.get(invoice.supplier_id ?? '') ??
                        t('adminPurchasing.unknownSupplier')}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {!invoicesLoading && invoices.length === 0 && (
              <div className="form-stack">
                <span className="page-subtitle">{t('adminPurchasing.selectInvoice')}</span>
                <PrimaryButton type="button" onClick={openCreateModal}>
                  {t('admin.newInvoice')}
                </PrimaryButton>
              </div>
            )}
            {invoiceId && (
              <div className="page-subtitle">
                {t('admin.workingInvoice', { id: invoiceId })}
              </div>
            )}
          </section>

          <section className="card">
            <div>
              <h3>{t('adminPurchasing.invoiceItems')}</h3>
              <p className="page-subtitle">{t('adminPurchasing.invoiceItemsSubtitle')}</p>
            </div>
            <div className="table-wrapper">
              <table className={invoiceDetailLoading ? 'table table--skeleton' : 'table'}>
                <thead>
                  <tr>
                    <th scope="col">{t('admin.table.name')}</th>
                    <th scope="col">{t('adminPurchasing.qty')}</th>
                    <th scope="col">{t('adminPurchasing.cost')}</th>
                    <th scope="col">{t('adminPurchasing.total')}</th>
                  </tr>
                </thead>
                <tbody>
                  {invoiceDetailLoading ? (
                    renderSkeletonRows(3, 4)
                  ) : invoiceDetail?.items?.length ? (
                    invoiceDetail.items.map((item) => (
                      <tr key={item.id}>
                        <td>{productMap.get(item.product_id) ?? '—'}</td>
                        <td>{item.quantity}</td>
                        <td>{item.unit_cost}</td>
                        <td>{Number(item.quantity) * Number(item.unit_cost)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4}>
                        <div className="form-stack">
                          <span className="page-subtitle">{t('adminPurchasing.emptyInvoiceItems')}</span>
                          <PrimaryButton type="button" onClick={openCreateModal}>
                            {t('adminPurchasing.addItemTitle')}
                          </PrimaryButton>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="form-row">
              <button className="danger" onClick={postInvoice} disabled={!invoiceId}>
                {t('admin.postInvoice')}
              </button>
            </div>
          </section>
        </div>
      )}

      {createModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>
                {createModalTab === 'suppliers'
                  ? t('adminPurchasing.createSupplier')
                  : t('adminPurchasing.addItemTitle')}
              </h4>
              <button className="ghost" onClick={closeCreateModal}>
                {t('common.cancel')}
              </button>
            </div>
            {createModalTab === 'suppliers' && (
              <div className="form-stack">
                <p className="page-subtitle">{t('adminPurchasing.createSupplierSubtitle')}</p>
                <div className="form-row">
                  <input
                    placeholder={t('admin.supplierPlaceholder')}
                    value={supplierName}
                    onChange={(e) => setSupplierName(e.target.value)}
                  />
                  <button onClick={createSupplier}>{t('admin.addSupplier')}</button>
                </div>
              </div>
            )}
            {createModalTab === 'invoices' && (
              <div className="form-stack">
                <div>
                  <h5>{t('adminPurchasing.workingInvoice')}</h5>
                  <p className="page-subtitle">{t('adminPurchasing.workingInvoiceSubtitle')}</p>
                </div>
                <label className="form-field">
                  <span>{t('adminPurchasing.selectSupplier')}</span>
                  <select
                    value={invoiceSupplierId}
                    onChange={(e) => setInvoiceSupplierId(e.target.value)}
                  >
                    <option value="">{t('admin.supplierPlaceholder')}</option>
                    {suppliers.map((supplier) => (
                      <option key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button onClick={createInvoice} disabled={!invoiceSupplierId}>
                  {t('admin.newInvoice')}
                </button>
                <div>
                  <h5>{t('adminPurchasing.addItemTitle')}</h5>
                  <p className="page-subtitle">{t('adminPurchasing.addItemSubtitle')}</p>
                </div>
                <div className="form-row">
                  <select
                    value={purchaseProduct}
                    onChange={(e) => setPurchaseProduct(e.target.value)}
                    disabled={productsLoading}
                  >
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
                    value={purchaseQty}
                    onChange={(e) => setPurchaseQty(e.target.value)}
                  />
                  <input
                    type="number"
                    min="0"
                    placeholder={t('admin.costPlaceholder')}
                    value={purchaseCost}
                    onChange={(e) => setPurchaseCost(e.target.value)}
                  />
                  <button onClick={addPurchaseItem} disabled={!invoiceId}>
                    {t('admin.addItem')}
                  </button>
                </div>
                {!invoiceId && (
                  <p className="page-subtitle">{t('adminPurchasing.selectInvoice')}</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
