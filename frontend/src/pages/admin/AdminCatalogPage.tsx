import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'

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
  cost_price: number
  sell_price: number
  image_url?: string | null
  category_id: string
  brand_id: string
  line_id?: string | null
}

type StockLevel = { product_id: string; on_hand: number }

type StockMove = {
  id: string
  product_id: string
  delta_qty: number
  reason: string
  reference: string
  created_at: string
}

type FastApiValidationError = { loc?: Array<string | number>; msg: string; type?: string }

type ApiErrorPayload = { detail?: string | FastApiValidationError[]; message?: string }

type CatalogTab = 'categories' | 'brands' | 'lines' | 'products'

export default function AdminCatalogPage() {
  const { t } = useTranslation()
  const { addToast } = useToast()
  const [activeTab, setActiveTab] = useState<CatalogTab>('categories')
  const [categories, setCategories] = useState<Category[]>([])
  const [brands, setBrands] = useState<Brand[]>([])
  const [lines, setLines] = useState<ProductLine[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [categoryName, setCategoryName] = useState('')
  const [brandName, setBrandName] = useState('')
  const [lineName, setLineName] = useState('')
  const [lineBrand, setLineBrand] = useState('')
  const [categoryLinkId, setCategoryLinkId] = useState('')
  const [categoryBrands, setCategoryBrands] = useState<Brand[]>([])
  const [categoryBrandsLoading, setCategoryBrandsLoading] = useState(false)
  const [categoryBrandsById, setCategoryBrandsById] = useState<Record<string, Brand[]>>({})
  const [categoryBrandsTableLoading, setCategoryBrandsTableLoading] = useState(false)
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
  const [productCostPrice, setProductCostPrice] = useState('0')
  const [productSellPrice, setProductSellPrice] = useState('0')
  const [productImageUrl, setProductImageUrl] = useState('')
  const [productCategoryBrands, setProductCategoryBrands] = useState<Brand[]>([])
  const [productBrandLines, setProductBrandLines] = useState<ProductLine[]>([])
  const [editOpen, setEditOpen] = useState(false)
  const [editType, setEditType] = useState<CatalogTab>('categories')
  const [editId, setEditId] = useState('')
  const [editName, setEditName] = useState('')
  const [editSku, setEditSku] = useState('')
  const [stockLevels, setStockLevels] = useState<StockLevel[]>([])
  const [stockLevelLoading, setStockLevelLoading] = useState(false)
  const [stockMoves, setStockMoves] = useState<StockMove[]>([])
  const [stockMovesLoading, setStockMovesLoading] = useState(false)
  const [editStockOnHand, setEditStockOnHand] = useState<number | null>(null)

  const categoryMap = useMemo(() => new Map(categories.map((item) => [item.id, item.name])), [categories])
  const brandMap = useMemo(() => new Map(brands.map((item) => [item.id, item.name])), [brands])
  const lineMap = useMemo(() => new Map(lines.map((item) => [item.id, item.name])), [lines])
  const stockMap = useMemo(
    () => new Map(stockLevels.map((item) => [item.product_id, item.on_hand])),
    [stockLevels]
  )

  const loadData = async () => {
    setCatalogLoading(true)
    try {
      const [cats, brs, lns, prods] = await Promise.all([
        api.get('/categories'),
        api.get('/brands'),
        api.get('/lines'),
        api.get('/products')
      ])
      setCategories(cats.data)
      setBrands(brs.data)
      setLines(lns.data)
      setProducts(prods.data)
    } catch (error) {
      addToast(getApiErrorMessage(error, t, 'common.error'), 'error')
    } finally {
      setCatalogLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (categories.length === 0) {
      setCategoryBrandsById({})
      return
    }
    const loadCategoryBrandsTable = async () => {
      setCategoryBrandsTableLoading(true)
      try {
        const responses = await Promise.all(
          categories.map((category) => api.get(`/categories/${category.id}/brands`))
        )
        const next = categories.reduce<Record<string, Brand[]>>((acc, category, index) => {
          acc[category.id] = responses[index].data
          return acc
        }, {})
        setCategoryBrandsById(next)
      } catch (error) {
        handleApiError(error)
      } finally {
        setCategoryBrandsTableLoading(false)
      }
    }
    void loadCategoryBrandsTable()
  }, [categories])

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

  const loadStockLevels = async () => {
    setStockLevelLoading(true)
    try {
      const res = await api.get('/stock')
      setStockLevels(res.data)
    } catch (error) {
      handleApiError(error)
    } finally {
      setStockLevelLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab !== 'products') return
    void loadStockLevels()
  }, [activeTab])

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

  const formatMoveType = (move: StockMove) => {
    if (move.reason === 'adjustment') {
      return t('adminStock.moveAdjust', { defaultValue: 'ADJUST' })
    }
    if (move.delta_qty >= 0) {
      return t('adminStock.moveIn', { defaultValue: 'IN' })
    }
    return t('adminStock.moveOut', { defaultValue: 'OUT' })
  }

  const formatMoveDate = (value: string) => {
    const parsed = new Date(value)
    if (Number.isNaN(parsed.valueOf())) return value
    return parsed.toLocaleString()
  }

  const confirmDeletion = () =>
    window.confirm(
      t('common.confirmDelete', { defaultValue: 'Are you sure you want to delete this item?' })
    )

  const loadCategoryBrands = async (
    categoryId: string,
    setter: (items: Brand[]) => void,
    setLoading?: (value: boolean) => void
  ) => {
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
    if (!editOpen || editType !== 'products' || !editId) {
      setStockMoves([])
      setEditStockOnHand(null)
      setStockMovesLoading(false)
      return
    }
    const loadProductStock = async () => {
      setStockMovesLoading(true)
      try {
        const [levelsRes, movesRes] = await Promise.all([
          api.get('/stock', { params: { product_id: editId } }),
          api.get('/stock/moves', { params: { product_id: editId } })
        ])
        const levels = levelsRes.data as StockLevel[]
        setEditStockOnHand(levels[0]?.on_hand ?? 0)
        setStockMoves(movesRes.data)
      } catch (error) {
        handleApiError(error)
      } finally {
        setStockMovesLoading(false)
      }
    }
    void loadProductStock()
  }, [editId, editOpen, editType])

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

  const deleteCategory = async (categoryId: string) => {
    if (!confirmDeletion()) {
      return
    }
    try {
      await api.delete(`/categories/${categoryId}`)
      addToast(t('common.deleted'), 'success')
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

  const deleteBrand = async (brandId: string) => {
    if (!confirmDeletion()) {
      return
    }
    try {
      await api.delete(`/brands/${brandId}`)
      addToast(t('common.deleted'), 'success')
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

  const deleteLine = async (lineId: string) => {
    if (!confirmDeletion()) {
      return
    }
    try {
      await api.delete(`/lines/${lineId}`)
      addToast(t('common.deleted'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const createProduct = async () => {
    const purchasePrice = Number(productPurchasePrice)
    const costPrice = Number(productCostPrice)
    const sellPrice = Number(productSellPrice)
    const trimmedName = productName.trim()

    if (!validateRequired([productCategoryId, productBrandId, productUnit])) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }

    if (!trimmedName && !productLineId) {
      addToast(
        t('admin.validation.productNameOrLine', {
          defaultValue: 'Введите название товара или выберите линейку'
        }),
        'error'
      )
      return
    }

    if (
      !Number.isFinite(purchasePrice) ||
      !Number.isFinite(costPrice) ||
      !Number.isFinite(sellPrice) ||
      purchasePrice < 0 ||
      costPrice < 0 ||
      sellPrice < 0
    ) {
      addToast(t('admin.validation.nonNegative'), 'error')
      return
    }

    try {
      await api.post('/products', {
        category_id: productCategoryId,
        brand_id: productBrandId,
        line_id: productLineId || null,
        name: trimmedName || null,
        sku: productSku.trim() || null,
        barcode: productBarcode.trim() || null,
        image_url: productImageUrl.trim() || null,
        unit: productUnit,
        purchase_price: purchasePrice,
        cost_price: costPrice,
        sell_price: sellPrice,
        tax_rate: 0
      })
      setProductName('')
      setProductSku('')
      setProductBarcode('')
      setProductUnit('pcs')
      setProductPurchasePrice('0')
      setProductCostPrice('0')
      setProductSellPrice('0')
      setProductImageUrl('')
      setProductLineId('')
      addToast(t('common.created'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const deleteProduct = async (productId: string) => {
    if (!confirmDeletion()) {
      return
    }
    try {
      await api.delete(`/products/${productId}`)
      addToast(t('common.deleted'), 'success')
      loadData()
    } catch (error) {
      handleApiError(error)
    }
  }

  const openEditModal = (type: CatalogTab, item: Category | Brand | ProductLine | Product) => {
    setEditType(type)
    setEditId(item.id)
    setEditName(item.name ?? '')
    if (type === 'products') {
      const product = item as Product
      setEditSku(product.sku ?? '')
    } else {
      setEditSku('')
    }
    setEditOpen(true)
  }

  const closeEditModal = () => {
    setEditOpen(false)
    setEditId('')
    setEditName('')
    setEditSku('')
  }

  const updateCategory = async (id: string, name: string) => {
    await api.patch(`/categories/${id}`, { name })
  }

  const updateBrand = async (id: string, name: string) => {
    await api.patch(`/brands/${id}`, { name })
  }

  const updateLine = async (id: string, name: string) => {
    await api.patch(`/lines/${id}`, { name })
  }

  const updateProduct = async (id: string, name: string, sku?: string) => {
    await api.patch(`/products/${id}`, { name, sku: sku?.trim() || null })
  }

  const handleEditSave = async () => {
    const trimmedName = editName.trim()
    if (!trimmedName) {
      addToast(t('admin.validation.requiredFields'), 'error')
      return
    }
    try {
      if (editType === 'categories') {
        await updateCategory(editId, trimmedName)
      } else if (editType === 'brands') {
        await updateBrand(editId, trimmedName)
      } else if (editType === 'lines') {
        await updateLine(editId, trimmedName)
      } else if (editType === 'products') {
        await updateProduct(editId, trimmedName, editSku)
      }
      addToast(t('common.updated', { defaultValue: 'Обновлено' }), 'success')
      closeEditModal()
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

  const canCreateCategory = categoryName.trim().length > 0
  const canCreateBrand = brandName.trim().length > 0
  const canCreateLine = lineName.trim().length > 0 && Boolean(lineBrand)
  const lineBrandMissing = !lineBrand
  const canCreateProduct =
    validateRequired([productCategoryId, productBrandId, productUnit]) &&
    isNonNegativeNumber(productPurchasePrice) &&
    isNonNegativeNumber(productCostPrice) &&
    isNonNegativeNumber(productSellPrice) &&
    (Boolean(productName.trim()) || Boolean(productLineId))

  const linkedBrandIds = new Set(categoryBrands.map((brand) => brand.id))
  const availableBrands = brands.filter((brand) => !linkedBrandIds.has(brand.id))
  const brandSearchTerm = brandSearch.trim().toLowerCase()
  const filteredAvailableBrands = availableBrands.filter((brand) =>
    brand.name.toLowerCase().includes(brandSearchTerm)
  )

  const handleProductImageUpload = (file?: File | null) => {
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setProductImageUrl(reader.result)
      }
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h2 className="page-title">{t('adminNav.catalog')}</h2>
        <p className="page-subtitle">{t('admin.catalogSubtitle')}</p>
      </div>
      <div className="tabs">
        <button
          type="button"
          className={activeTab === 'categories' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('categories')}
        >
          {t('adminTabs.categories')}
        </button>
        <button
          type="button"
          className={activeTab === 'brands' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('brands')}
        >
          {t('adminTabs.brands')}
        </button>
        <button
          type="button"
          className={activeTab === 'lines' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('lines')}
        >
          {t('adminTabs.lines')}
        </button>
        <button
          type="button"
          className={activeTab === 'products' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('products')}
        >
          {t('adminTabs.products')}
        </button>
      </div>

      {activeTab === 'categories' && (
        <div className="split">
          <section className="card">
            <div>
              <h3>{t('adminSections.createCategory')}</h3>
              <p className="page-subtitle">{t('adminSections.createCategorySubtitle')}</p>
            </div>
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
          </section>
          <section className="card">
            <h3>{t('adminSections.categoryList')}</h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">{t('admin.table.name')}</th>
                    <th scope="col">{t('admin.table.brands')}</th>
                    <th scope="col">{t('admin.table.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {catalogLoading ? (
                    <tr>
                      <td colSpan={3}>{t('common.loading')}</td>
                    </tr>
                  ) : categories.length === 0 ? (
                    <tr>
                      <td colSpan={3}>{t('admin.emptyCategories')}</td>
                    </tr>
                  ) : (
                    categories.map((category) => (
                      <tr key={category.id}>
                        <td>{category.name}</td>
                        <td>
                          {categoryBrandsTableLoading
                            ? t('common.loading')
                            : categoryBrandsById[category.id]?.length
                              ? categoryBrandsById[category.id].map((brand) => brand.name).join(', ')
                              : t('admin.emptyCategoryBrands')}
                        </td>
                        <td>
                          <button
                            className="secondary"
                            onClick={() => openEditModal('categories', category)}
                          >
                            {t('common.edit', { defaultValue: 'Редактировать' })}
                          </button>
                          <button className="secondary" onClick={() => deleteCategory(category.id)}>
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
        </div>
      )}

      {activeTab === 'brands' && (
        <div className="split">
          <section className="card">
            <div>
              <h3>{t('adminSections.createBrand')}</h3>
              <p className="page-subtitle">{t('adminSections.createBrandSubtitle')}</p>
            </div>
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
          </section>
          <section className="card">
            <h3>{t('adminSections.brandList')}</h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">{t('admin.table.name')}</th>
                    <th scope="col">{t('admin.table.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {catalogLoading ? (
                    <tr>
                      <td colSpan={2}>{t('common.loading')}</td>
                    </tr>
                  ) : brands.length === 0 ? (
                    <tr>
                      <td colSpan={2}>{t('admin.emptyBrands')}</td>
                    </tr>
                  ) : (
                    brands.map((brand) => (
                      <tr key={brand.id}>
                        <td>{brand.name}</td>
                        <td>
                          <button
                            className="secondary"
                            onClick={() => openEditModal('brands', brand)}
                          >
                            {t('common.edit', { defaultValue: 'Редактировать' })}
                          </button>
                          <button className="secondary" onClick={() => deleteBrand(brand.id)}>
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
        </div>
      )}

      {activeTab === 'lines' && (
        <div className="split">
          <section className="card">
            <div>
              <h3>{t('adminSections.createLine')}</h3>
              <p className="page-subtitle">{t('adminSections.createLineSubtitle')}</p>
            </div>
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
              <button
                onClick={createLine}
                disabled={!canCreateLine}
                title={lineBrandMissing ? t('admin.validation.selectBrandForLine') : undefined}
              >
                {t('admin.addLine')}
              </button>
            </div>
            {lineBrandMissing && <p className="page-subtitle">{t('admin.validation.selectBrandForLine')}</p>}
          </section>
          <section className="card">
            <h3>{t('adminSections.lineList')}</h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">{t('admin.table.name')}</th>
                    <th scope="col">{t('admin.table.brand')}</th>
                    <th scope="col">{t('admin.table.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {catalogLoading ? (
                    <tr>
                      <td colSpan={3}>{t('common.loading')}</td>
                    </tr>
                  ) : lines.length === 0 ? (
                    <tr>
                      <td colSpan={3}>{t('admin.emptyLines')}</td>
                    </tr>
                  ) : (
                    lines.map((line) => (
                      <tr key={line.id}>
                        <td>{line.name}</td>
                        <td>{brandMap.get(line.brand_id) ?? '—'}</td>
                        <td>
                          <button
                            className="secondary"
                            onClick={() => openEditModal('lines', line)}
                          >
                            {t('common.edit', { defaultValue: 'Редактировать' })}
                          </button>
                          <button className="secondary" onClick={() => deleteLine(line.id)}>
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
        </div>
      )}

      {activeTab === 'products' && (
        <div className="split">
          <section className="card">
            <div>
              <h3>{t('adminSections.createProduct')}</h3>
              <p className="page-subtitle">{t('adminSections.createProductSubtitle')}</p>
            </div>
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
              <p className="page-subtitle">
                {t('admin.productNameHelp', {
                  defaultValue: 'Можно оставить пустым — возьмём название из линейки.'
                })}
              </p>
              <div className="form-row">
                <label className="form-field">
                  <span>{t('admin.productImageLabel')}</span>
                  <input
                    type="url"
                    placeholder={t('admin.productImagePlaceholder')}
                    value={productImageUrl}
                    onChange={(e) => setProductImageUrl(e.target.value)}
                  />
                </label>
                <label className="form-field">
                  <span>{t('admin.productImageUpload')}</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleProductImageUpload(e.target.files?.[0])}
                  />
                </label>
                {productImageUrl && (
                  <div className="image-preview">
                    <img src={productImageUrl} alt={t('admin.productImagePreview')} />
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => setProductImageUrl('')}
                    >
                      {t('admin.clearImage')}
                    </button>
                  </div>
                )}
              </div>
              <div className="form-row">
                <label className="form-field">
                  <span>{t('admin.unitLabel')}</span>
                  <select value={productUnit} onChange={(e) => setProductUnit(e.target.value)}>
                    <option value="pcs">{t('admin.unitPcs')}</option>
                    <option value="ml">{t('admin.unitMl')}</option>
                    <option value="g">{t('admin.unitG')}</option>
                  </select>
                </label>
                <label className="form-field">
                  <span>{t('admin.purchasePriceLabel')}</span>
                  <input
                    type="number"
                    min="0"
                    placeholder={t('admin.purchasePricePlaceholder')}
                    value={productPurchasePrice}
                    onChange={(e) => setProductPurchasePrice(e.target.value)}
                  />
                </label>
                <label className="form-field">
                  <span>{t('admin.costPriceLabel')}</span>
                  <input
                    type="number"
                    min="0"
                    placeholder={t('admin.costPricePlaceholder')}
                    value={productCostPrice}
                    onChange={(e) => setProductCostPrice(e.target.value)}
                  />
                </label>
                <label className="form-field">
                  <span>{t('admin.sellPriceLabel')}</span>
                  <input
                    type="number"
                    min="0"
                    placeholder={t('admin.sellPricePlaceholder')}
                    value={productSellPrice}
                    onChange={(e) => setProductSellPrice(e.target.value)}
                  />
                </label>
                <button onClick={createProduct} disabled={!canCreateProduct}>
                  {t('admin.saveProduct')}
                </button>
              </div>
            </div>
          </section>
          <section className="card">
            <h3>{t('adminSections.productList')}</h3>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">{t('admin.table.image')}</th>
                    <th scope="col">{t('admin.table.name')}</th>
                    <th scope="col">{t('admin.table.sku')}</th>
                    <th scope="col">{t('admin.table.category')}</th>
                    <th scope="col">{t('admin.table.brand')}</th>
                    <th scope="col">{t('admin.table.line')}</th>
                    <th scope="col">{t('admin.table.unit')}</th>
                    <th scope="col">{t('admin.table.purchasePrice')}</th>
                    <th scope="col">{t('admin.table.costPrice')}</th>
                    <th scope="col">{t('admin.table.sellPrice')}</th>
                    <th scope="col">{t('adminStock.onHand', { defaultValue: 'On hand' })}</th>
                    <th scope="col">{t('admin.table.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {catalogLoading ? (
                    <tr>
                      <td colSpan={12}>{t('common.loading')}</td>
                    </tr>
                  ) : products.length === 0 ? (
                    <tr>
                      <td colSpan={12}>{t('admin.emptyProducts')}</td>
                    </tr>
                  ) : (
                    products.map((product) => (
                      <tr key={product.id}>
                        <td>
                          {product.image_url ? (
                            <img
                              src={product.image_url}
                              alt={product.name}
                              className="table-image"
                            />
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                        <td>{product.name}</td>
                        <td>{product.sku || '—'}</td>
                        <td>{categoryMap.get(product.category_id) ?? '—'}</td>
                        <td>{brandMap.get(product.brand_id) ?? '—'}</td>
                        <td>{product.line_id ? lineMap.get(product.line_id) ?? '—' : '—'}</td>
                        <td>{product.unit}</td>
                        <td>{product.purchase_price}</td>
                        <td>{product.cost_price}</td>
                        <td>{product.sell_price}</td>
                        <td>
                          {stockLevelLoading
                            ? t('common.loading')
                            : stockMap.get(product.id) ?? 0}
                        </td>
                        <td>
                          <button
                            className="secondary"
                            onClick={() => openEditModal('products', product)}
                          >
                            {t('common.edit', { defaultValue: 'Редактировать' })}
                          </button>
                          <button className="secondary" onClick={() => deleteProduct(product.id)}>
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
        </div>
      )}

      {editOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('common.edit', { defaultValue: 'Редактировать' })}</h4>
              <button className="ghost" onClick={closeEditModal}>
                {t('common.cancel')}
              </button>
            </div>
            <div className="form-stack">
              <input
                placeholder={t('admin.table.name')}
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
              {editType === 'products' && (
                <input
                  placeholder={t('admin.skuPlaceholder')}
                  value={editSku}
                  onChange={(e) => setEditSku(e.target.value)}
                />
              )}
              {editType === 'products' && (
                <div className="form-stack">
                  <div>
                    <h5>{t('adminStock.movesTitle', { defaultValue: 'Stock moves' })}</h5>
                    <p className="page-subtitle">
                      {t('adminStock.movesSubtitle', { defaultValue: 'History of stock changes for this product.' })}
                    </p>
                  </div>
                  <div className="form-row">
                    <span className="muted">
                      {t('adminStock.onHand', { defaultValue: 'On hand' })}
                    </span>
                    <strong>
                      {editStockOnHand === null ? t('common.loading') : editStockOnHand}
                    </strong>
                  </div>
                  <div className="table-wrapper">
                    <table className="table">
                      <thead>
                        <tr>
                          <th scope="col">{t('adminStock.moveDate', { defaultValue: 'Date' })}</th>
                          <th scope="col">{t('adminStock.moveType', { defaultValue: 'Type' })}</th>
                          <th scope="col">{t('adminStock.moveQty', { defaultValue: 'Qty' })}</th>
                          <th scope="col">{t('adminStock.moveReason', { defaultValue: 'Reason' })}</th>
                          <th scope="col">{t('adminStock.moveReference', { defaultValue: 'Reference' })}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stockMovesLoading ? (
                          <tr>
                            <td colSpan={5}>{t('common.loading')}</td>
                          </tr>
                        ) : stockMoves.length === 0 ? (
                          <tr>
                            <td colSpan={5}>
                              {t('adminStock.movesEmpty', { defaultValue: 'No stock moves yet.' })}
                            </td>
                          </tr>
                        ) : (
                          stockMoves.map((move) => (
                            <tr key={move.id}>
                              <td>{formatMoveDate(move.created_at)}</td>
                              <td>{formatMoveType(move)}</td>
                              <td>{Math.abs(move.delta_qty)}</td>
                              <td>{move.reason}</td>
                              <td>{move.reference || '—'}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              <div className="form-row">
                <button onClick={handleEditSave}>{t('common.save', { defaultValue: 'Сохранить' })}</button>
                <button className="ghost" onClick={closeEditModal}>
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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
