import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import api from '../api/client'
import { useTenantSettings } from '../api/tenantSettings'
import { useTranslation } from 'react-i18next'
import { getApiErrorMessage } from '../utils/apiError'
import { useToast } from '../components/ToastProvider'

type Category = { id: string; name: string }
type Brand = { id: string; name: string }
type ProductLine = { id: string; name: string; brand_id: string }
type Product = {
  id: string
  name: string
  sku?: string | null
  barcode?: string | null
  unit: string
  purchase_price: number
  sell_price: number
  category_id: string
  brand_id: string
  line_id?: string | null
}
type Supplier = { id: string; name: string }

type ApiErrorPayload = { detail?: string; message?: string }

export default function AdminDashboard() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const { data: tenantSettings } = useTenantSettings()
  const [categories, setCategories] = useState<Category[]>([])
  const [brands, setBrands] = useState<Brand[]>([])
  const [lines, setLines] = useState<ProductLine[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [categoryName, setCategoryName] = useState('')
  const [brandName, setBrandName] = useState('')
  const [lineName, setLineName] = useState('')
  const [lineBrand, setLineBrand] = useState('')
  const [categoryLinkId, setCategoryLinkId] = useState('')
  const [categoryBrands, setCategoryBrands] = useState<Brand[]>([])
  const [categoryBrandsLoading, setCategoryBrandsLoading] = useState(false)
  const [linkModalOpen, setLinkModalOpen] = useState(false)
  const [brandSearch, setBrandSearch] = useState('')
  const [productCategoryId, setProductCategoryId] = useState('')
  const [productBrandId, setProductBrandId] = useState('')
  const [productLineId, setProductLineId] = useState('')
  const [productName, setProductName] = useState('')
  const [productSku, setProductSku] = useState('')
  const [productBarcode, setProductBarcode] = useState('')
  const [productUnit, setProductUnit] = useState('pcs')
  const [productPurchasePrice, setProductPurchasePrice] = useState('0')
  const [productSellPrice, setProductSellPrice] = useState('0')
  const [productCategoryBrands, setProductCategoryBrands] = useState<Brand[]>([])
  const [productBrandLines, setProductBrandLines] = useState<ProductLine[]>([])
  const [supplierName, setSupplierName] = useState('')
  const [invoiceId, setInvoiceId] = useState('')
  const [purchaseProduct, setPurchaseProduct] = useState('')
  const [purchaseQty, setPurchaseQty] = useState('0')
  const [purchaseCost, setPurchaseCost] = useState('0')
  const [stockProduct, setStockProduct] = useState('')
  const [stockQty, setStockQty] = useState('0')
  const [reports, setReports] = useState<any>(null)

  const categoryMap = useMemo(() => new Map(categories.map((item) => [item.id, item.name])), [categories])
  const brandMap = useMemo(() => new Map(brands.map((item) => [item.id, item.name])), [brands])
  const lineMap = useMemo(() => new Map(lines.map((item) => [item.id, item.name])), [lines])

  const loadData = async () => {
    setCatalogLoading(true)
    try {
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
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    } finally {
      setCatalogLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

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
        addToast(detail || t('common.error'), 'error')
        return
      }
    }
    addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
  }

  const validateRequired = (fields: Array<string | number | null | undefined>) =>
    fields.every((field) => {
      if (typeof field === 'number') {
        return Number.isFinite(field)
      }
      return Boolean(String(field ?? '').trim())
    })

  const isNonNegativeNumber = (value: string) => {
    const parsed = Number(value)
    return Number.isFinite(parsed) && parsed >= 0
  }

  const loadCategoryBrands = async (categoryId: string, setter: (brands: Brand[]) => void, setLoading?: (value: boolean) => void) => {
    if (!categoryId) {
      setter([])
      return
    }
    try {
      setLoading?.(true)
      const res = await api.get(`/categories/${categoryId}/brands`)
      setter(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setLoading?.(false)
    }
  }

  useEffect(() => {
    void loadCategoryBrands(categoryLinkId, setCategoryBrands, setCategoryBrandsLoading)
  }, [categoryLinkId])

  useEffect(() => {
    setProductBrandId('')
    setProductLineId('')
    setProductBrandLines([])
    if (!productCategoryId) {
      setProductCategoryBrands([])
      return
    }
    void loadCategoryBrands(productCategoryId, setProductCategoryBrands)
  }, [productCategoryId])

  useEffect(() => {
    setProductLineId('')
    if (!productBrandId) {
      setProductBrandLines([])
      return
    }
    const loadLines = async () => {
      try {
        const res = await api.get('/lines', { params: { brand_id: productBrandId } })
        setProductBrandLines(res.data)
      } catch (error) {
        handleApiError(error)
      }
    }
    void loadLines()
  }, [productBrandId])

  const createCategory = async () => {
    if (!categoryName.trim()) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post('/categories', { name: categoryName.trim() })
      setCategoryName('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const createBrand = async () => {
    if (!brandName.trim()) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post('/brands', { name: brandName.trim() })
      setBrandName('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const createLine = async () => {
    if (!lineName.trim() || !lineBrand) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post('/lines', { name: lineName.trim(), brand_id: lineBrand })
      setLineName('')
      setLineBrand('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const createProduct = async () => {
    const purchasePrice = Number(productPurchasePrice)
    const sellPrice = Number(productSellPrice)

    if (!validateRequired([productCategoryId, productBrandId, productName, productUnit])) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }

    if (!Number.isFinite(purchasePrice) || !Number.isFinite(sellPrice) || purchasePrice < 0 || sellPrice < 0) {
      addToast(t('admin.validation.nonNegative'), 'error')
      return
    }

    try {
      await api.post('/products', {
        category_id: productCategoryId,
        brand_id: productBrandId,
        line_id: productLineId || null,
        name: productName.trim(),
        sku: productSku.trim() || null,
        barcode: productBarcode.trim() || null,
        unit: productUnit,
        purchase_price: purchasePrice,
        sell_price: sellPrice,
        tax_rate: 0
      })
      setProductName('')
      setProductSku('')
      setProductBarcode('')
      setProductUnit('pcs')
      setProductPurchasePrice('0')
      setProductSellPrice('0')
      setProductLineId('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const linkBrandToCategory = async (brandId: string) => {
    if (!categoryLinkId) {
      return
    }
    try {
      await api.post(`/categories/${categoryLinkId}/brands/${brandId}`)
      addToast(t('common.created'), 'success')
      loadCategoryBrands(categoryLinkId, setCategoryBrands)
      if (productCategoryId === categoryLinkId) {
        loadCategoryBrands(productCategoryId, setProductCategoryBrands)
      }
    } catch (error) {
      handleApiError(error)
    }
  }

  const unlinkBrandFromCategory = async (brandId: string) => {
    if (!categoryLinkId) {
      return
    }
    try {
      await api.delete(`/categories/${categoryLinkId}/brands/${brandId}`)
      addToast(t('common.deleted'), 'success')
      loadCategoryBrands(categoryLinkId, setCategoryBrands)
      if (productCategoryId === categoryLinkId) {
        loadCategoryBrands(productCategoryId, setProductCategoryBrands)
      }
    } catch (error) {
      handleApiError(error)
    }
  }

  const createSupplier = async () => {
    if (!supplierName.trim()) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post('/suppliers', { name: supplierName.trim() })
      setSupplierName('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const createInvoice = async () => {
    try {
      const res = await api.post('/purchase-invoices', { supplier_id: suppliers[0]?.id })
      setInvoiceId(res.data.id)
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const addPurchaseItem = async () => {
    if (!invoiceId) return
    if (!purchaseProduct || !isNonNegativeNumber(purchaseQty) || !isNonNegativeNumber(purchaseCost)) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      await api.post(`/purchase-invoices/${invoiceId}/items`, {
        product_id: purchaseProduct,
        quantity: purchaseQty,
        unit_cost: purchaseCost
      })
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const postInvoice = async () => {
    if (invoiceId) {
      try {
        await api.post(`/purchase-invoices/${invoiceId}/post`)
        addToast(t('common.updated'), 'success')
        loadData()
      } catch (error) {
        handleApiError(error)
      }
    }
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
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const loadReports = async () => {
    try {
      const res = await api.get('/reports/summary')
      setReports(res.data)
      addToast(t('common.saved'), 'success')
    } catch (error) {
      handleApiError(error)
    }
  }

  const reportsEnabled =
    tenantSettings?.features.find((feature) => feature.code === 'reports')?.is_enabled ?? true
  const reportsModuleEnabled =
    tenantSettings?.modules.find((module) => module.code === 'reports')?.is_enabled ?? true
  const showReports = reportsEnabled && reportsModuleEnabled

  const linkedBrandIds = new Set(categoryBrands.map((brand) => brand.id))
  const availableBrands = brands.filter((brand) => !linkedBrandIds.has(brand.id))
  const brandSearchTerm = brandSearch.trim().toLowerCase()
  const filteredAvailableBrands = availableBrands.filter((brand) =>
    brand.name.toLowerCase().includes(brandSearchTerm)
  )

  const canCreateCategory = categoryName.trim().length > 0
  const canCreateBrand = brandName.trim().length > 0
  const canCreateLine = lineName.trim().length > 0 && Boolean(lineBrand)
  const canCreateProduct =
    validateRequired([productCategoryId, productBrandId, productName, productUnit]) &&
    isNonNegativeNumber(productPurchasePrice) &&
    isNonNegativeNumber(productSellPrice)

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">{t('admin.title')}</h2>
      </div>
      <div className="grid grid-cards">
        <section className="card">
          <div>
            <h3>{t('admin.catalog')}</h3>
            <p className="page-subtitle">{t('admin.catalogSubtitle')}</p>
          </div>
          <div className="form-stack">
            <div>
              <h4>{t('admin.catalogCategoryTitle')}</h4>
              <div className="form-row">
                <input
                  placeholder={t('admin.categoryPlaceholder')}
                  value={categoryName}
                  onChange={(e) => setCategoryName(e.target.value)}
                />
                <button onClick={createCategory} disabled={!canCreateCategory}>
                  {t('admin.addCategory')}
                </button>
              </div>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">{t('admin.table.name')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalogLoading ? (
                      <tr>
                        <td>{t('common.loading')}</td>
                      </tr>
                    ) : categories.length === 0 ? (
                      <tr>
                        <td>{t('admin.emptyCategories')}</td>
                      </tr>
                    ) : (
                      categories.map((category) => (
                        <tr key={category.id}>
                          <td>{category.name}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4>{t('admin.catalogBrandTitle')}</h4>
              <div className="form-row">
                <input
                  placeholder={t('admin.brandPlaceholder')}
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                />
                <button onClick={createBrand} disabled={!canCreateBrand}>
                  {t('admin.addBrand')}
                </button>
              </div>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">{t('admin.table.name')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalogLoading ? (
                      <tr>
                        <td>{t('common.loading')}</td>
                      </tr>
                    ) : brands.length === 0 ? (
                      <tr>
                        <td>{t('admin.emptyBrands')}</td>
                      </tr>
                    ) : (
                      brands.map((brand) => (
                        <tr key={brand.id}>
                          <td>{brand.name}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4>{t('admin.catalogLinkTitle')}</h4>
              <div className="form-row">
                <select value={categoryLinkId} onChange={(e) => setCategoryLinkId(e.target.value)}>
                  <option value="">{t('admin.categorySelect')}</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <button
                  className="ghost"
                  onClick={() => setLinkModalOpen(true)}
                  disabled={!categoryLinkId}
                >
                  {t('admin.linkBrand')}
                </button>
              </div>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">{t('admin.table.brand')}</th>
                      <th scope="col">{t('admin.table.actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryBrandsLoading ? (
                      <tr>
                        <td colSpan={2}>{t('common.loading')}</td>
                      </tr>
                    ) : categoryLinkId && categoryBrands.length === 0 ? (
                      <tr>
                        <td colSpan={2}>{t('admin.emptyLinkedBrands')}</td>
                      </tr>
                    ) : !categoryLinkId ? (
                      <tr>
                        <td colSpan={2}>{t('admin.selectCategoryToLink')}</td>
                      </tr>
                    ) : (
                      categoryBrands.map((brand) => (
                        <tr key={brand.id}>
                          <td>{brand.name}</td>
                          <td>
                            <button className="secondary" onClick={() => unlinkBrandFromCategory(brand.id)}>
                              {t('admin.unlinkBrand')}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4>{t('admin.catalogLineTitle')}</h4>
              <div className="form-row">
                <input
                  placeholder={t('admin.linePlaceholder')}
                  value={lineName}
                  onChange={(e) => setLineName(e.target.value)}
                />
                <select value={lineBrand} onChange={(e) => setLineBrand(e.target.value)}>
                  <option value="">{t('admin.brandSelect')}</option>
                  {brands.map((brand) => (
                    <option key={brand.id} value={brand.id}>
                      {brand.name}
                    </option>
                  ))}
                </select>
                <button onClick={createLine} disabled={!canCreateLine}>
                  {t('admin.addLine')}
                </button>
              </div>
            </div>

            <div>
              <h4>{t('admin.catalogProductTitle')}</h4>
              <div className="form-stack">
                <select value={productCategoryId} onChange={(e) => setProductCategoryId(e.target.value)}>
                  <option value="">{t('admin.categorySelect')}</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                <select
                  value={productBrandId}
                  onChange={(e) => setProductBrandId(e.target.value)}
                  disabled={!productCategoryId}
                >
                  <option value="">{t('admin.brandSelect')}</option>
                  {productCategoryBrands.map((brand) => (
                    <option key={brand.id} value={brand.id}>
                      {brand.name}
                    </option>
                  ))}
                </select>
                <select
                  value={productLineId}
                  onChange={(e) => setProductLineId(e.target.value)}
                  disabled={!productBrandId}
                >
                  <option value="">{t('admin.lineSelect')}</option>
                  {productBrandLines.map((line) => (
                    <option key={line.id} value={line.id}>
                      {line.name}
                    </option>
                  ))}
                </select>
                <div className="form-row">
                  <input
                    placeholder={t('admin.productPlaceholder')}
                    value={productName}
                    onChange={(e) => setProductName(e.target.value)}
                  />
                  <input
                    placeholder={t('admin.skuPlaceholder')}
                    value={productSku}
                    onChange={(e) => setProductSku(e.target.value)}
                  />
                  <input
                    placeholder={t('admin.barcodePlaceholder')}
                    value={productBarcode}
                    onChange={(e) => setProductBarcode(e.target.value)}
                  />
                </div>
                <div className="form-row">
                  <select value={productUnit} onChange={(e) => setProductUnit(e.target.value)}>
                    <option value="pcs">{t('admin.unitPcs')}</option>
                    <option value="ml">{t('admin.unitMl')}</option>
                    <option value="g">{t('admin.unitG')}</option>
                  </select>
                  <input
                    type="number"
                    min="0"
                    placeholder={t('admin.purchasePricePlaceholder')}
                    value={productPurchasePrice}
                    onChange={(e) => setProductPurchasePrice(e.target.value)}
                  />
                  <input
                    type="number"
                    min="0"
                    placeholder={t('admin.sellPricePlaceholder')}
                    value={productSellPrice}
                    onChange={(e) => setProductSellPrice(e.target.value)}
                  />
                  <button onClick={createProduct} disabled={!canCreateProduct}>
                    {t('admin.addProduct')}
                  </button>
                </div>
              </div>
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">{t('admin.table.name')}</th>
                      <th scope="col">{t('admin.table.sku')}</th>
                      <th scope="col">{t('admin.table.category')}</th>
                      <th scope="col">{t('admin.table.brand')}</th>
                      <th scope="col">{t('admin.table.line')}</th>
                      <th scope="col">{t('admin.table.unit')}</th>
                      <th scope="col">{t('admin.table.purchasePrice')}</th>
                      <th scope="col">{t('admin.table.sellPrice')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalogLoading ? (
                      <tr>
                        <td colSpan={8}>{t('common.loading')}</td>
                      </tr>
                    ) : products.length === 0 ? (
                      <tr>
                        <td colSpan={8}>{t('admin.emptyProducts')}</td>
                      </tr>
                    ) : (
                      products.map((product) => (
                        <tr key={product.id}>
                          <td>{product.name}</td>
                          <td>{product.sku || '—'}</td>
                          <td>{categoryMap.get(product.category_id) ?? '—'}</td>
                          <td>{brandMap.get(product.brand_id) ?? '—'}</td>
                          <td>{product.line_id ? lineMap.get(product.line_id) ?? '—' : '—'}</td>
                          <td>{product.unit}</td>
                          <td>{product.purchase_price}</td>
                          <td>{product.sell_price}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
        <section className="card">
          <h3>{t('admin.suppliersPurchasing')}</h3>
          <div className="form-stack">
            <div className="form-row">
              <input
                placeholder={t('admin.supplierPlaceholder')}
                value={supplierName}
                onChange={(e) => setSupplierName(e.target.value)}
              />
              <button onClick={createSupplier}>{t('admin.addSupplier')}</button>
            </div>
            <div className="form-row">
              <button onClick={createInvoice}>{t('admin.newInvoice')}</button>
              {invoiceId && <div className="page-subtitle">{t('admin.workingInvoice', { id: invoiceId })}</div>}
            </div>
            <div className="form-row">
              <select value={purchaseProduct} onChange={(e) => setPurchaseProduct(e.target.value)}>
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
          <h4>{t('admin.stockLevels')}</h4>
          <ul className="pill-list">
            {products.map((product) => (
              <li key={product.id} className="pill">
                {product.name}
              </li>
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
      {linkModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('admin.linkBrandModalTitle')}</h4>
              <button
                className="ghost"
                onClick={() => {
                  setLinkModalOpen(false)
                  setBrandSearch('')
                }}
              >
                {t('common.cancel')}
              </button>
            </div>
            <div className="form-stack">
              <input
                placeholder={t('admin.searchBrandPlaceholder')}
                value={brandSearch}
                onChange={(e) => setBrandSearch(e.target.value)}
              />
              <div className="table-wrapper">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">{t('admin.table.brand')}</th>
                      <th scope="col">{t('admin.table.actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAvailableBrands.length === 0 ? (
                      <tr>
                        <td colSpan={2}>{t('admin.emptyAvailableBrands')}</td>
                      </tr>
                    ) : (
                      filteredAvailableBrands.map((brand) => (
                        <tr key={brand.id}>
                          <td>{brand.name}</td>
                          <td>
                            <button
                              onClick={() => linkBrandToCategory(brand.id)}
                              disabled={!categoryLinkId}
                            >
                              {t('admin.linkBrand')}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
