import { useEffect, useState } from 'react'
import api from '../api/client'
import { useTenantSettings } from '../api/tenantSettings'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

type Category = { id: string; name: string }
type Brand = { id: string; name: string }
type ProductLine = { id: string; name: string; brand_id: string }
type Product = { id: string; name: string; price: number }
type Supplier = { id: string; name: string }

export default function AdminDashboard() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const { data: tenantSettings } = useTenantSettings()
  const [categories, setCategories] = useState<Category[]>([])
  const [brands, setBrands] = useState<Brand[]>([])
  const [lines, setLines] = useState<ProductLine[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [categoryName, setCategoryName] = useState('')
  const [brandName, setBrandName] = useState('')
  const [lineName, setLineName] = useState('')
  const [lineBrand, setLineBrand] = useState('')
  const [productName, setProductName] = useState('')
  const [productPrice, setProductPrice] = useState('0')
  const [productSku, setProductSku] = useState('')
  const [supplierName, setSupplierName] = useState('')
  const [invoiceId, setInvoiceId] = useState('')
  const [purchaseProduct, setPurchaseProduct] = useState('')
  const [purchaseQty, setPurchaseQty] = useState('0')
  const [purchaseCost, setPurchaseCost] = useState('0')
  const [stockProduct, setStockProduct] = useState('')
  const [stockQty, setStockQty] = useState('0')
  const [reports, setReports] = useState<any>(null)

  const loadData = async () => {
    const [cats, brs, lns, prods, sups] = await Promise.all([
      api.get('/categories'),
      api.get('/brands'),
      api.get('/lines'),
      api.get('/products'),
      api.get('/suppliers')
    ])
    setCategories(cats.data)
    setBrands(brs.data)
    setLines(lns.data)
    setProducts(prods.data)
    setSuppliers(sups.data)
  }

  useEffect(() => {
    loadData()
  }, [])

  const createCategory = async () => {
    if (!categoryName.trim()) return
    try {
      await api.post('/categories', { name: categoryName })
      setCategoryName('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const createBrand = async () => {
    if (!brandName.trim()) return
    try {
      await api.post('/brands', { name: brandName })
      setBrandName('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const createLine = async () => {
    if (!lineName.trim()) return
    try {
      await api.post('/lines', { name: lineName, brand_id: lineBrand })
      setLineName('')
      setLineBrand('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const createProduct = async () => {
    if (!productName.trim()) return
    try {
      await api.post('/products', { name: productName, price: Number(productPrice), sku: productSku })
      setProductName('')
      setProductPrice('0')
      setProductSku('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const createSupplier = async () => {
    if (!supplierName.trim()) return
    try {
      await api.post('/suppliers', { name: supplierName })
      setSupplierName('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const createInvoice = async () => {
    try {
      const res = await api.post('/purchase-invoices', { supplier_id: suppliers[0]?.id })
      setInvoiceId(res.data.id)
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const addPurchaseItem = async () => {
    if (!invoiceId) return
    try {
      await api.post(`/purchase-invoices/${invoiceId}/items`, {
        product_id: purchaseProduct,
        quantity: purchaseQty,
        unit_cost: purchaseCost
      })
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const postInvoice = async () => {
    if (invoiceId) {
      try {
        await api.post(`/purchase-invoices/${invoiceId}/post`)
        addToast(t('common.updated'), 'success')
        loadData()
      } catch (error) {
        addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
      }
    }
  }

  const adjustStock = async () => {
    try {
      await api.post('/stock/adjustments', { product_id: stockProduct, quantity: Number(stockQty), reason: 'adjustment' })
      addToast(t('common.updated'), 'success')
      loadData()
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const loadReports = async () => {
    try {
      const res = await api.get('/reports/summary')
      setReports(res.data)
      addToast(t('common.saved'), 'success')
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    }
  }

  const reportsEnabled =
    tenantSettings?.features.find((feature) => feature.code === 'reports')?.is_enabled ?? true
  const reportsModuleEnabled =
    tenantSettings?.modules.find((module) => module.code === 'reports')?.is_enabled ?? true
  const showReports = reportsEnabled && reportsModuleEnabled

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">{t('admin.title')}</h2>
      </div>
      <div className="grid grid-cards">
        <section className="card">
          <h3>{t('admin.catalog')}</h3>
          <div className="form-stack">
            <div className="form-row">
              <input placeholder={t('admin.categoryPlaceholder')} value={categoryName} onChange={(e) => setCategoryName(e.target.value)} />
              <button onClick={createCategory}>{t('admin.addCategory')}</button>
            </div>
            <div className="form-row">
              <input placeholder={t('admin.brandPlaceholder')} value={brandName} onChange={(e) => setBrandName(e.target.value)} />
              <button onClick={createBrand}>{t('admin.addBrand')}</button>
            </div>
            <div className="form-row">
              <input placeholder={t('admin.linePlaceholder')} value={lineName} onChange={(e) => setLineName(e.target.value)} />
              <select value={lineBrand} onChange={(e) => setLineBrand(e.target.value)}>
                <option value="">{t('admin.brandSelect')}</option>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
              <button onClick={createLine}>{t('admin.addLine')}</button>
            </div>
            <div className="form-row">
              <input placeholder={t('admin.skuPlaceholder')} value={productSku} onChange={(e) => setProductSku(e.target.value)} />
              <input placeholder={t('admin.productPlaceholder')} value={productName} onChange={(e) => setProductName(e.target.value)} />
              <input placeholder={t('admin.pricePlaceholder')} value={productPrice} onChange={(e) => setProductPrice(e.target.value)} />
              <button onClick={createProduct}>{t('admin.addProduct')}</button>
            </div>
          </div>
          <ul className="pill-list">
            {products.map((p) => (
              <li key={p.id} className="pill">{p.name}</li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h3>{t('admin.suppliersPurchasing')}</h3>
          <div className="form-stack">
            <div className="form-row">
              <input placeholder={t('admin.supplierPlaceholder')} value={supplierName} onChange={(e) => setSupplierName(e.target.value)} />
              <button onClick={createSupplier}>{t('admin.addSupplier')}</button>
            </div>
            <div className="form-row">
              <button onClick={createInvoice}>{t('admin.newInvoice')}</button>
              {invoiceId && <div className="page-subtitle">{t('admin.workingInvoice', { id: invoiceId })}</div>}
            </div>
            <div className="form-row">
              <select value={purchaseProduct} onChange={(e) => setPurchaseProduct(e.target.value)}>
                <option value="">{t('admin.productSelect')}</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <input placeholder={t('admin.qtyPlaceholder')} value={purchaseQty} onChange={(e) => setPurchaseQty(e.target.value)} />
              <input placeholder={t('admin.costPlaceholder')} value={purchaseCost} onChange={(e) => setPurchaseCost(e.target.value)} />
              <button onClick={addPurchaseItem}>{t('admin.addItem')}</button>
            </div>
            <button onClick={postInvoice}>{t('admin.postInvoice')}</button>
          </div>
        </section>
        <section className="card">
          <h3>{t('admin.stock')}</h3>
          <div className="form-stack">
            <select value={stockProduct} onChange={(e) => setStockProduct(e.target.value)}>
              <option value="">{t('admin.productSelect')}</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <input placeholder={t('admin.qtyPlaceholder')} value={stockQty} onChange={(e) => setStockQty(e.target.value)} />
            <button onClick={adjustStock}>{t('admin.adjust')}</button>
          </div>
          <h4>{t('admin.stockLevels')}</h4>
          <ul className="pill-list">
            {products.map((p) => (
              <li key={p.id} className="pill">{p.name}</li>
            ))}
          </ul>
        </section>
        {showReports && (
          <section className="card">
            <h3>{t('admin.reports')}</h3>
            <button onClick={loadReports}>{t('admin.loadSummary')}</button>
            {reports && (
              <div className="table-wrapper">
                <table className="table">
                  <tbody>
                    <tr>
                      <th scope="row">{t('admin.totalSales')}</th>
                      <td>{reports.total_sales}</td>
                    </tr>
                    <tr>
                      <th scope="row">{t('admin.totalPurchases')}</th>
                      <td>{reports.total_purchases}</td>
                    </tr>
                    <tr>
                      <th scope="row">{t('admin.grossMargin')}</th>
                      <td>{reports.gross_margin}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  )
}
