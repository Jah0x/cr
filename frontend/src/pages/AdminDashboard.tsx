import { useEffect, useState } from 'react'
import api from '../api/client'
import { useTenantSettings } from '../api/tenantSettings'
import { useTranslation } from 'react-i18next'

type Category = { id: string; name: string }
type Brand = { id: string; name: string }
type ProductLine = { id: string; name: string; brand_id: string }
type Product = { id: string; name: string; price: number }
type Supplier = { id: string; name: string }

export default function AdminDashboard() {
  const { t } = useTranslation()
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
    await api.post('/categories', { name: categoryName })
    setCategoryName('')
    loadData()
  }

  const createBrand = async () => {
    await api.post('/brands', { name: brandName })
    setBrandName('')
    loadData()
  }

  const createLine = async () => {
    await api.post('/lines', { name: lineName, brand_id: lineBrand })
    setLineName('')
    setLineBrand('')
    loadData()
  }

  const createProduct = async () => {
    await api.post('/products', { name: productName, price: Number(productPrice), sku: productSku })
    setProductName('')
    setProductPrice('0')
    setProductSku('')
    loadData()
  }

  const createSupplier = async () => {
    await api.post('/suppliers', { name: supplierName })
    setSupplierName('')
    loadData()
  }

  const createInvoice = async () => {
    const res = await api.post('/purchase-invoices', { supplier_id: suppliers[0]?.id })
    setInvoiceId(res.data.id)
    loadData()
  }

  const addPurchaseItem = async () => {
    if (!invoiceId) return
    await api.post(`/purchase-invoices/${invoiceId}/items`, {
      product_id: purchaseProduct,
      quantity: purchaseQty,
      unit_cost: purchaseCost
    })
    loadData()
  }

  const postInvoice = async () => {
    if (invoiceId) {
      await api.post(`/purchase-invoices/${invoiceId}/post`)
      loadData()
    }
  }

  const adjustStock = async () => {
    await api.post('/stock/adjustments', { product_id: stockProduct, quantity: Number(stockQty), reason: 'adjustment' })
    loadData()
  }

  const loadReports = async () => {
    const res = await api.get('/reports/summary')
    setReports(res.data)
  }

  const reportsEnabled =
    tenantSettings?.features.find((feature) => feature.code === 'reports')?.is_enabled ?? true
  const reportsModuleEnabled =
    tenantSettings?.modules.find((module) => module.code === 'reports')?.is_enabled ?? true
  const showReports = reportsEnabled && reportsModuleEnabled

  return (
    <div style={{ padding: 24 }}>
      <h2>{t('admin.title')}</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('admin.catalog')}</h3>
          <input placeholder={t('admin.categoryPlaceholder')} value={categoryName} onChange={(e) => setCategoryName(e.target.value)} />
          <button onClick={createCategory}>{t('admin.addCategory')}</button>
          <input placeholder={t('admin.brandPlaceholder')} value={brandName} onChange={(e) => setBrandName(e.target.value)} />
          <button onClick={createBrand}>{t('admin.addBrand')}</button>
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
          <input placeholder={t('admin.skuPlaceholder')} value={productSku} onChange={(e) => setProductSku(e.target.value)} />
          <input placeholder={t('admin.productPlaceholder')} value={productName} onChange={(e) => setProductName(e.target.value)} />
          <input placeholder={t('admin.pricePlaceholder')} value={productPrice} onChange={(e) => setProductPrice(e.target.value)} />
          <button onClick={createProduct}>{t('admin.addProduct')}</button>
          <ul>
            {products.map((p) => (
              <li key={p.id}>{p.name}</li>
            ))}
          </ul>
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('admin.suppliersPurchasing')}</h3>
          <input placeholder={t('admin.supplierPlaceholder')} value={supplierName} onChange={(e) => setSupplierName(e.target.value)} />
          <button onClick={createSupplier}>{t('admin.addSupplier')}</button>
          <button onClick={createInvoice}>{t('admin.newInvoice')}</button>
          {invoiceId && <p>{t('admin.workingInvoice', { id: invoiceId })}</p>}
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
          <button onClick={postInvoice}>{t('admin.postInvoice')}</button>
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>{t('admin.stock')}</h3>
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
          <h4>{t('admin.stockLevels')}</h4>
          <ul>
            {products.map((p) => (
              <li key={p.id}>{p.name}</li>
            ))}
          </ul>
        </div>
        {showReports && (
          <div style={{ background: '#fff', padding: 12 }}>
            <h3>{t('admin.reports')}</h3>
            <button onClick={loadReports}>{t('admin.loadSummary')}</button>
            {reports && (
              <div>
                <p>{t('admin.totalSales')}: {reports.total_sales}</p>
                <p>{t('admin.totalPurchases')}: {reports.total_purchases}</p>
                <p>{t('admin.grossMargin')}: {reports.gross_margin}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
