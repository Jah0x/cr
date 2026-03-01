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

type InvoiceStatusFilter = 'all' | 'draft' | 'posted' | 'void'

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
  const [invoiceStatusFilter, setInvoiceStatusFilter] = useState<InvoiceStatusFilter>('draft')
  const [invoiceSearch, setInvoiceSearch] = useState('')
  const [selectedInvoiceIds, setSelectedInvoiceIds] = useState<string[]>([])
  const [purchaseProduct, setPurchaseProduct] = useState('')
  const [purchaseQty, setPurchaseQty] = useState('1')
  const [purchaseCost, setPurchaseCost] = useState('')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createModalTab, setCreateModalTab] = useState<PurchasingTab>('suppliers')

  const productMap = useMemo(() => new Map(products.map((item) => [item.id, item.name])), [products])
  const supplierMap = useMemo(() => new Map(suppliers.map((item) => [item.id, item.name])), [suppliers])

  const formatNumber = (value: number | string, maximumFractionDigits = 2) => {
    const numericValue = Number(value)
    if (!Number.isFinite(numericValue)) {
      return '0'
    }
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 0,
      maximumFractionDigits
    }).format(numericValue)
  }

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
      const statusParam = invoiceStatusFilter === 'all' ? undefined : invoiceStatusFilter
      const res = await api.get('/purchase-invoices', {
        params: statusParam ? { status: statusParam } : undefined
      })
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
  }, [])

  useEffect(() => {
    void loadInvoices()
  }, [invoiceStatusFilter])

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
      setPurchaseQty('1')
      setPurchaseCost('')
      setInvoiceDetail(res.data)
      addToast(t('common.created'), 'success')
      loadInvoices()
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

  const voidInvoice = async () => {
    if (!invoiceId) {
      addToast(t('adminPurchasing.selectInvoice'), 'error')
      return
    }
    try {
      await api.post(`/purchase-invoices/${invoiceId}/void`)
      addToast(t('common.updated'), 'success')
      setInvoiceId('')
      setInvoiceDetail(null)
      loadInvoices()
    } catch (error) {
      handleApiError(error)
    }
  }

  const deleteInvoice = async (targetInvoiceId?: string) => {
    const id = targetInvoiceId ?? invoiceId
    if (!id) {
      addToast(t('adminPurchasing.selectInvoice'), 'error')
      return
    }
    if (!confirmDeletion()) {
      return
    }
    try {
      await api.delete(`/purchase-invoices/${id}`)
      addToast(t('common.deleted'), 'success')
      if (id === invoiceId) {
        setInvoiceId('')
        setInvoiceDetail(null)
      }
      setSelectedInvoiceIds((prev) => prev.filter((item) => item !== id))
      loadInvoices()
    } catch (error) {
      handleApiError(error)
    }
  }

  const processSelectedInvoices = async (action: 'post' | 'void' | 'delete') => {
    if (selectedInvoiceIds.length === 0) {
      addToast(t('adminPurchasing.selectInvoice'), 'error')
      return
    }
    if (action === 'delete' && !confirmDeletion()) {
      return
    }

    const failures: string[] = []
    for (const id of selectedInvoiceIds) {
      try {
        if (action === 'post') {
          await api.post(`/purchase-invoices/${id}/post`)
        } else if (action === 'void') {
          await api.post(`/purchase-invoices/${id}/void`)
        } else {
          await api.delete(`/purchase-invoices/${id}`)
        }
      } catch {
        failures.push(id.slice(0, 8))
      }
    }

    if (failures.length) {
      addToast(
        t('adminPurchasing.bulkActionFailed', {
          defaultValue: `Не удалось обработать накладные: ${failures.join(', ')}`
        }),
        'error'
      )
    } else {
      addToast(t('common.updated'), 'success')
    }

    setSelectedInvoiceIds([])
    if (invoiceId && selectedInvoiceIds.includes(invoiceId)) {
      setInvoiceId('')
      setInvoiceDetail(null)
    }
    loadInvoices()
  }

  const openCreateModal = () => {
    setCreateModalTab(activeTab)
    setCreateModalOpen(true)
  }

  const closeCreateModal = () => {
    setCreateModalOpen(false)
  }

  const toggleInvoiceSelection = (id: string) => {
    setSelectedInvoiceIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
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

  const filteredInvoices = useMemo(
    () =>
      invoices.filter((invoice) => {
        const search = invoiceSearch.trim().toLowerCase()
        if (!search) {
          return true
        }
        const supplierName = supplierMap.get(invoice.supplier_id ?? '')?.toLowerCase() ?? ''
        return invoice.id.toLowerCase().includes(search) || supplierName.includes(search)
      }),
    [invoiceSearch, invoices, supplierMap]
  )

  useEffect(() => {
    setSelectedInvoiceIds((prev) => prev.filter((id) => filteredInvoices.some((invoice) => invoice.id === id)))
  }, [filteredInvoices])

  const invoiceTotal =
    invoiceDetail?.items?.reduce((sum, item) => sum + Number(item.quantity) * Number(item.unit_cost), 0) ?? 0

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
                <span>{t('adminPurchasing.statusFilter')}</span>
                <select
                  value={invoiceStatusFilter}
                  onChange={(e) => setInvoiceStatusFilter(e.target.value as InvoiceStatusFilter)}
                >
                  <option value="all">{t('adminPurchasing.statusAll')}</option>
                  <option value="draft">{t('adminPurchasing.statusDraft')}</option>
                  <option value="posted">{t('adminPurchasing.statusPosted')}</option>
                  <option value="void">{t('adminPurchasing.statusVoid')}</option>
                </select>
              </label>
              <label className="form-field">
                <span>{t('adminPurchasing.searchField')}</span>
                <input
                  placeholder={t('adminPurchasing.searchPlaceholder')}
                  value={invoiceSearch}
                  onChange={(e) => setInvoiceSearch(e.target.value)}
                />
              </label>
              <label className="form-field">
                <span>{t('adminPurchasing.selectInvoice')}</span>
                <select
                  value={invoiceId}
                  onChange={(e) => setInvoiceId(e.target.value)}
                  disabled={invoicesLoading}
                >
                  <option value="">{t('adminPurchasing.selectInvoicePlaceholder')}</option>
                  {filteredInvoices.map((invoice) => (
                    <option key={invoice.id} value={invoice.id}>
                      {invoice.id.slice(0, 8)} ·{' '}
                      {supplierMap.get(invoice.supplier_id ?? '') ??
                        t('adminPurchasing.unknownSupplier')}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {filteredInvoices.length > 0 && (
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">
                        <input
                          type="checkbox"
                          checked={filteredInvoices.length > 0 && selectedInvoiceIds.length === filteredInvoices.length}
                          onChange={(e) =>
                            setSelectedInvoiceIds(e.target.checked ? filteredInvoices.map((invoice) => invoice.id) : [])
                          }
                        />
                      </th>
                      <th scope="col">ID</th>
                      <th scope="col">{t('admin.table.name')}</th>
                      <th scope="col">{t('common.status')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInvoices.map((invoice) => (
                      <tr key={invoice.id}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedInvoiceIds.includes(invoice.id)}
                            onChange={() => toggleInvoiceSelection(invoice.id)}
                          />
                        </td>
                        <td>{invoice.id.slice(0, 8)}</td>
                        <td>{supplierMap.get(invoice.supplier_id ?? '') ?? t('adminPurchasing.unknownSupplier')}</td>
                        <td>{invoice.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="form-row">
                  <button
                    type="button"
                    className="danger"
                    disabled={selectedInvoiceIds.length === 0}
                    onClick={() => processSelectedInvoices('post')}
                  >
                    {t('admin.postInvoice', { defaultValue: 'Провести накладную' })} ({selectedInvoiceIds.length})
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={selectedInvoiceIds.length === 0}
                    onClick={() => processSelectedInvoices('void')}
                  >
                    {t('adminPurchasing.voidInvoice')} ({selectedInvoiceIds.length})
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={selectedInvoiceIds.length === 0}
                    onClick={() => processSelectedInvoices('delete')}
                  >
                    {t('common.delete')} ({selectedInvoiceIds.length})
                  </button>
                </div>
              </div>
            )}

            {!invoicesLoading && filteredInvoices.length === 0 && (
              <div className="form-stack">
                <span className="page-subtitle">{t('adminPurchasing.selectInvoice')}</span>
                <PrimaryButton type="button" onClick={openCreateModal}>
                  {t('admin.newInvoice')}
                </PrimaryButton>
              </div>
            )}
            {invoiceId && (
              <div className="form-row">
                <div className="page-subtitle">
                  {t('admin.workingInvoice', { id: invoiceId })}
                </div>
                <button type="button" className="secondary" onClick={loadInvoices}>
                  {t('common.retry')}
                </button>
              </div>
            )}

            <div className="form-stack">
              <div>
                <h4>{t('adminPurchasing.addItemTitle')}</h4>
                <p className="page-subtitle">{t('adminPurchasing.addItemSubtitle')}</p>
              </div>
              <div className="form-row">
                <label className="form-field">
                  <span>{t('adminPurchasing.productField')}</span>
                  <select
                    value={purchaseProduct}
                    onChange={(e) => setPurchaseProduct(e.target.value)}
                    disabled={productsLoading || !invoiceId}
                  >
                    <option value="">{t('adminPurchasing.productSelectPlaceholder')}</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="form-field">
                  <span>{t('adminPurchasing.qtyField')}</span>
                  <input
                    type="number"
                    min="1"
                    step="0.001"
                    placeholder={t('adminPurchasing.qtyPlaceholderDetailed')}
                    value={purchaseQty}
                    onChange={(e) => setPurchaseQty(e.target.value)}
                    disabled={!invoiceId}
                  />
                </label>
                <label className="form-field">
                  <span>{t('adminPurchasing.costField')}</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder={t('adminPurchasing.costPlaceholderDetailed')}
                    value={purchaseCost}
                    onChange={(e) => setPurchaseCost(e.target.value)}
                    disabled={!invoiceId}
                  />
                </label>
                <PrimaryButton type="button" onClick={addPurchaseItem} disabled={!invoiceId}>
                  {t('admin.addItem')}
                </PrimaryButton>
              </div>
              {!invoiceId && <p className="page-subtitle">{t('adminPurchasing.selectInvoice')}</p>}
            </div>
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
                        <td>{formatNumber(item.quantity, 3)}</td>
                        <td>{formatNumber(item.unit_cost)}</td>
                        <td>{formatNumber(Number(item.quantity) * Number(item.unit_cost))}</td>
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
            {Boolean(invoiceDetail) && (
              <div className="form-row">
                <div className="form-field">
                  <span>{t('adminPurchasing.itemsCount')}</span>
                  <strong>{invoiceDetail?.items?.length ?? 0}</strong>
                </div>
                <div className="form-field">
                  <span>{t('adminPurchasing.total')}</span>
                  <strong>{formatNumber(invoiceTotal)}</strong>
                </div>
                <div className="form-field">
                  <span>{t('common.status')}</span>
                  <strong>{invoiceDetail?.status ?? '—'}</strong>
                </div>
              </div>
            )}
            <div className="form-row">
              <button className="danger" onClick={postInvoice} disabled={!invoiceId}>
                {t('admin.postInvoice')}
              </button>
              <button className="secondary" onClick={voidInvoice} disabled={!invoiceId}>
                {t('adminPurchasing.voidInvoice')}
              </button>
              <button className="secondary" onClick={() => deleteInvoice()} disabled={!invoiceId}>
                {t('common.delete')}
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
                  : t('admin.newInvoice')}
              </h4>
              <button className="ghost" onClick={closeCreateModal}>
                {t('common.close')}
              </button>
            </div>
            {createModalTab === 'suppliers' && (
              <div className="form-stack">
                <p className="page-subtitle">{t('adminPurchasing.createSupplierSubtitle')}</p>
                <div className="form-row">
                  <input
                    placeholder={t('adminPurchasing.supplierNamePlaceholder')}
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
                    <option value="">{t('adminPurchasing.supplierSelectPlaceholder')}</option>
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
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
