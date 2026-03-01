import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { useTranslation } from 'react-i18next'
import api from '../../api/client'
import { useToast } from '../../components/ToastProvider'
import { getApiErrorMessage } from '../../utils/apiError'
import { PrimaryButton } from '../../components/Buttons'
import PageTitle from '../../components/PageTitle'

type Category = { id: string; name: string }

type Brand = { id: string; name: string }

type ProductLine = { id: string; name: string; brand_id: string }

type Product = {
  id: string
  name: string
  sku?: string | null
  barcode?: string | null
  unit: string
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
type ProductSort = 'name_asc' | 'name_desc' | 'stock_desc' | 'stock_asc' | 'price_desc' | 'price_asc' | 'name_length_desc'

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
  const [linkModalColumns, setLinkModalColumns] = useState<1 | 2>(1)
  const [productCategoryId, setProductCategoryId] = useState('')
  const [productBrandId, setProductBrandId] = useState('')
  const [productLineId, setProductLineId] = useState('')
  const [productName, setProductName] = useState('')
  const [productSku, setProductSku] = useState('')
  const [productBarcode, setProductBarcode] = useState('')
  const [productUnit, setProductUnit] = useState('pcs')
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
  const [editBarcode, setEditBarcode] = useState('')
  const [editUnit, setEditUnit] = useState('pcs')
  const [editCostPrice, setEditCostPrice] = useState('0')
  const [editSellPrice, setEditSellPrice] = useState('0')
  const [editImageUrl, setEditImageUrl] = useState('')
  const [editCategoryId, setEditCategoryId] = useState('')
  const [editBrandId, setEditBrandId] = useState('')
  const [editLineId, setEditLineId] = useState('')
  const [editCategoryBrands, setEditCategoryBrands] = useState<Brand[]>([])
  const [editBrandLines, setEditBrandLines] = useState<ProductLine[]>([])
  const [stockLevels, setStockLevels] = useState<StockLevel[]>([])
  const [stockLevelLoading, setStockLevelLoading] = useState(false)
  const [stockMoves, setStockMoves] = useState<StockMove[]>([])
  const [stockMovesLoading, setStockMovesLoading] = useState(false)
  const [editStockOnHand, setEditStockOnHand] = useState<number | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createModalTab, setCreateModalTab] = useState<CatalogTab>('categories')
  const [productSort, setProductSort] = useState<ProductSort>('name_asc')

  const categoryMap = useMemo(() => new Map(categories.map((item) => [item.id, item.name])), [categories])
  const brandMap = useMemo(() => new Map(brands.map((item) => [item.id, item.name])), [brands])
  const lineMap = useMemo(() => new Map(lines.map((item) => [item.id, item.name])), [lines])
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
  const sortedCategories = useMemo(
    () => [...categories].sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })),
    [categories]
  )
  const sortedBrands = useMemo(
    () => [...brands].sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })),
    [brands]
  )
  const sortedLines = useMemo(
    () => [...lines].sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })),
    [lines]
  )
  const stockMap = useMemo(
    () => new Map(stockLevels.map((item) => [item.product_id, item.on_hand])),
    [stockLevels]
  )
  const sortedProducts = useMemo(() => {
    const collator = new Intl.Collator(undefined, { sensitivity: 'base' })
    return [...products].sort((a, b) => {
      if (productSort === 'name_desc') return collator.compare(b.name, a.name)
      if (productSort === 'stock_desc') return (stockMap.get(b.id) ?? 0) - (stockMap.get(a.id) ?? 0)
      if (productSort === 'stock_asc') return (stockMap.get(a.id) ?? 0) - (stockMap.get(b.id) ?? 0)
      if (productSort === 'price_desc') return Number(b.sell_price) - Number(a.sell_price)
      if (productSort === 'price_asc') return Number(a.sell_price) - Number(b.sell_price)
      if (productSort === 'name_length_desc') return b.name.length - a.name.length
      return collator.compare(a.name, b.name)
    })
  }, [productSort, products, stockMap])

  const loadData = async () => {
    setCatalogLoading(true)
    const [cats, brs, lns, prods] = await Promise.allSettled([
      api.get('/categories'),
      api.get('/brands'),
      api.get('/lines'),
      api.get('/products')
    ])

    setCategories(cats.status === 'fulfilled' ? cats.value.data : [])
    setBrands(brs.status === 'fulfilled' ? brs.value.data : [])
    setLines(lns.status === 'fulfilled' ? lns.value.data : [])
    setProducts(prods.status === 'fulfilled' ? prods.value.data : [])

    const firstFailure = [cats, brs, lns, prods].find((result) => result.status === 'rejected')
    if (firstFailure?.status === 'rejected') {
      addToast(getApiErrorMessage(firstFailure.reason, t, 'common.error'), 'error')
    }

    setCatalogLoading(false)
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
    if (!editOpen || editType !== 'products') {
      return
    }
    if (!editCategoryId) {
      setEditCategoryBrands([])
      return
    }
    void loadCategoryBrands(editCategoryId, setEditCategoryBrands)
  }, [editCategoryId, editOpen, editType])

  useEffect(() => {
    if (!editOpen || editType !== 'products') {
      return
    }
    if (!editBrandId) {
      setEditBrandLines([])
      return
    }
    const loadLines = async () => {
      try {
        const res = await api.get('/lines', { params: { brand_id: editBrandId } })
        setEditBrandLines(res.data)
      } catch (error) {
        handleApiError(error)
      }
    }
    void loadLines()
  }, [editBrandId, editOpen, editType])

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
      setCreateModalOpen(false)
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
      setCreateModalOpen(false)
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
      setCreateModalOpen(false)
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
      !Number.isFinite(costPrice) ||
      !Number.isFinite(sellPrice) ||
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
        purchase_price: 0,
        cost_price: costPrice,
        sell_price: sellPrice,
        tax_rate: 0
      })
      setProductName('')
      setProductSku('')
      setProductBarcode('')
      setProductUnit('pcs')
      setProductCostPrice('0')
      setProductSellPrice('0')
      setProductImageUrl('')
      setProductLineId('')
      addToast(t('common.created'), 'success')
      loadData()
      setCreateModalOpen(false)
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

  const deleteAllProducts = async () => {
    if (products.length === 0 || !confirmDeletion()) {
      return
    }
    try {
      await api.delete('/products')
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
      setEditBarcode(product.barcode ?? '')
      setEditUnit(product.unit ?? 'pcs')
      setEditCostPrice(String(product.cost_price ?? 0))
      setEditSellPrice(String(product.sell_price ?? 0))
      setEditImageUrl(product.image_url ?? '')
      setEditCategoryId(product.category_id ?? '')
      setEditBrandId(product.brand_id ?? '')
      setEditLineId(product.line_id ?? '')
    } else {
      setEditSku('')
      setEditBarcode('')
      setEditUnit('pcs')
      setEditCostPrice('0')
      setEditSellPrice('0')
      setEditImageUrl('')
      setEditCategoryId('')
      setEditBrandId('')
      setEditLineId('')
    }
    setEditOpen(true)
  }

  const closeEditModal = () => {
    setEditOpen(false)
    setEditId('')
    setEditName('')
    setEditSku('')
    setEditBarcode('')
    setEditUnit('pcs')
    setEditCostPrice('0')
    setEditSellPrice('0')
    setEditImageUrl('')
    setEditCategoryId('')
    setEditBrandId('')
    setEditLineId('')
    setEditCategoryBrands([])
    setEditBrandLines([])
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

  const updateProduct = async (id: string, payload: Record<string, unknown>) => {
    await api.patch(`/products/${id}`, payload)
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
        const costPrice = Number(editCostPrice)
        const sellPrice = Number(editSellPrice)

        if (!validateRequired([editCategoryId, editBrandId, editUnit])) {
          addToast(t('admin.validation.requiredFields'), 'error')
          return
        }

        if (!trimmedName && !editLineId) {
          addToast(
            t('admin.validation.productNameOrLine', {
              defaultValue: 'Введите название товара или выберите линейку'
            }),
            'error'
          )
          return
        }

        if (
              !Number.isFinite(costPrice) ||
          !Number.isFinite(sellPrice) ||
              costPrice < 0 ||
          sellPrice < 0
        ) {
          addToast(t('admin.validation.nonNegative'), 'error')
          return
        }

        await updateProduct(editId, {
          name: trimmedName || null,
          sku: editSku.trim() || null,
          barcode: editBarcode.trim() || null,
          unit: editUnit,
          purchase_price: 0,
          cost_price: costPrice,
          sell_price: sellPrice,
          image_url: editImageUrl.trim() || null,
          category_id: editCategoryId,
          brand_id: editBrandId,
          line_id: editLineId || null
        })
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

  const unlinkAllBrandsFromCategory = async () => {
    if (!categoryLinkId || categoryBrands.length === 0 || !confirmDeletion()) {
      return
    }
    try {
      await Promise.all(categoryBrands.map((brand) => api.delete(`/categories/${categoryLinkId}/brands/${brand.id}`)))
      addToast(t('common.deleted'), 'success')
      loadCategoryBrands(categoryLinkId, setCategoryBrands)
      loadData()
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
    isNonNegativeNumber(productCostPrice) &&
    isNonNegativeNumber(productSellPrice) &&
    (Boolean(productName.trim()) || Boolean(productLineId))

  const linkedBrandIds = new Set(categoryBrands.map((brand) => brand.id))
  const availableBrands = sortedBrands.filter((brand) => !linkedBrandIds.has(brand.id))
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

  const handleEditImageUpload = (file?: File | null) => {
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setEditImageUrl(reader.result)
      }
    }
    reader.readAsDataURL(file)
  }

  const openCreateModal = () => {
    openCreateModalFor(activeTab)
  }

  const closeCreateModal = () => {
    setCreateModalOpen(false)
  }

  const openCreateModalFor = (tab: CatalogTab) => {
    setCreateModalTab(tab)
    setCreateModalOpen(true)
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
        title={t('adminNav.catalog')}
        subtitle={t('admin.catalogSubtitle')}
        actions={
          <PrimaryButton type="button" onClick={openCreateModal}>
            {t('common.add', { defaultValue: 'Добавить' })}
          </PrimaryButton>
        }
      />
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
        <div className="split" style={{ gridTemplateColumns: '320px minmax(0, 1fr)' }}>
          <section className="card">
            <div>
              <h4>{t('admin.catalogLinkTitle')}</h4>
              <div className="form-row">
                <select value={categoryLinkId} onChange={(e) => setCategoryLinkId(e.target.value)}>
                  <option value="">{t('admin.categorySelect')}</option>
                  {sortedCategories.map((category) => (
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
                <button
                  className="ghost"
                  onClick={unlinkAllBrandsFromCategory}
                  disabled={!categoryLinkId || categoryBrands.length === 0}
                >
                  {t('common.deleteAll', { defaultValue: 'Удалить все' })}
                </button>
              </div>
              <div className="table-wrapper">
                <table className={categoryBrandsLoading ? 'table table--skeleton' : 'table'}>
                  <thead>
                    <tr>
                      <th scope="col">{t('admin.table.brand')}</th>
                      <th scope="col">{t('admin.table.actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryBrandsLoading ? (
                      renderSkeletonRows(3, 2)
                    ) : categoryLinkId && categoryBrands.length === 0 ? (
                      <tr>
                        <td colSpan={2}>
                          <div className="form-stack">
                            <span className="page-subtitle">{t('admin.emptyLinkedBrands')}</span>
                            <button
                              className="secondary"
                              onClick={() => setLinkModalOpen(true)}
                              disabled={!categoryLinkId}
                            >
                              {t('admin.linkBrand')}
                            </button>
                          </div>
                        </td>
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
              <table className={catalogLoading ? 'table table--skeleton' : 'table'}>
                <thead>
                  <tr>
                    <th scope="col">{t('admin.table.name')}</th>
                    <th scope="col">{t('admin.table.brands')}</th>
                    <th scope="col">{t('admin.table.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {catalogLoading ? (
                    renderSkeletonRows(4, 3)
                  ) : categories.length === 0 ? (
                    <tr>
                      <td colSpan={3}>
                        <div className="form-stack">
                          <span className="page-subtitle">{t('admin.emptyCategories')}</span>
                          <PrimaryButton type="button" onClick={() => openCreateModalFor('categories')}>
                            {t('adminSections.createCategory')}
                          </PrimaryButton>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    sortedCategories.map((category) => (
                      <tr key={category.id}>
                        <td>{category.name}</td>
                        <td>
                          {categoryBrandsTableLoading ? (
                            <span className="skeleton skeleton-text" />
                          ) : categoryBrandsById[category.id]?.length ? (
                            categoryBrandsById[category.id].map((brand) => brand.name).join(', ')
                          ) : (
                            t('admin.emptyCategoryBrands')
                          )}
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
        <section className="card">
          <h3>{t('adminSections.brandList')}</h3>
          <div className="table-wrapper">
            <table className={catalogLoading ? 'table table--skeleton' : 'table'}>
              <thead>
                <tr>
                  <th scope="col">{t('admin.table.name')}</th>
                  <th scope="col">{t('admin.table.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {catalogLoading ? (
                  renderSkeletonRows(4, 2)
                ) : brands.length === 0 ? (
                  <tr>
                    <td colSpan={2}>
                      <div className="form-stack">
                        <span className="page-subtitle">{t('admin.emptyBrands')}</span>
                        <PrimaryButton type="button" onClick={() => openCreateModalFor('brands')}>
                          {t('adminSections.createBrand')}
                        </PrimaryButton>
                      </div>
                    </td>
                  </tr>
                ) : (
                  sortedBrands.map((brand) => (
                    <tr key={brand.id}>
                      <td>{brand.name}</td>
                      <td>
                        <button className="secondary" onClick={() => openEditModal('brands', brand)}>
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
      )}

      {activeTab === 'lines' && (
        <section className="card">
          <h3>{t('adminSections.lineList')}</h3>
          <div className="table-wrapper">
            <table className={catalogLoading ? 'table table--skeleton' : 'table'}>
              <thead>
                <tr>
                  <th scope="col">{t('admin.table.name')}</th>
                  <th scope="col">{t('admin.table.brand')}</th>
                  <th scope="col">{t('admin.table.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {catalogLoading ? (
                  renderSkeletonRows(4, 3)
                ) : lines.length === 0 ? (
                  <tr>
                    <td colSpan={3}>
                      <div className="form-stack">
                        <span className="page-subtitle">{t('admin.emptyLines')}</span>
                        <PrimaryButton type="button" onClick={() => openCreateModalFor('lines')}>
                          {t('adminSections.createLine')}
                        </PrimaryButton>
                      </div>
                    </td>
                  </tr>
                ) : (
                  sortedLines.map((line) => (
                    <tr key={line.id}>
                      <td>{line.name}</td>
                      <td>{brandMap.get(line.brand_id) ?? '—'}</td>
                      <td>
                        <button className="secondary" onClick={() => openEditModal('lines', line)}>
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
      )}

      {activeTab === 'products' && (
        <section className="card">
          <div className="form-row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
            <h3>{t('adminSections.productList')}</h3>
            <div className="form-row" style={{ gap: 8 }}>
              <select value={productSort} onChange={(event) => setProductSort(event.target.value as ProductSort)}>
                <option value="name_asc">{t('admin.productSort.nameAsc', { defaultValue: 'Название A→Я' })}</option>
                <option value="name_desc">{t('admin.productSort.nameDesc', { defaultValue: 'Название Я→A' })}</option>
                <option value="stock_desc">{t('admin.productSort.stockDesc', { defaultValue: 'Остаток: больше сначала' })}</option>
                <option value="stock_asc">{t('admin.productSort.stockAsc', { defaultValue: 'Остаток: меньше сначала' })}</option>
                <option value="price_desc">{t('admin.productSort.priceDesc', { defaultValue: 'Цена: дороже сначала' })}</option>
                <option value="price_asc">{t('admin.productSort.priceAsc', { defaultValue: 'Цена: дешевле сначала' })}</option>
                <option value="name_length_desc">{t('admin.productSort.nameLengthDesc', { defaultValue: 'По длине названия' })}</option>
              </select>
              <button className="secondary" onClick={deleteAllProducts} disabled={products.length === 0}>
                {t('common.deleteAll', { defaultValue: 'Удалить все' })}
              </button>
            </div>
          </div>
          <div className="table-wrapper">
            <table className={catalogLoading ? 'table table--skeleton' : 'table'}>
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
                  renderSkeletonRows(4, 12)
                ) : products.length === 0 ? (
                  <tr>
                    <td colSpan={12}>
                      <div className="form-stack">
                        <span className="page-subtitle">{t('admin.emptyProducts')}</span>
                        <PrimaryButton type="button" onClick={() => openCreateModalFor('products')}>
                          {t('adminSections.createProduct')}
                        </PrimaryButton>
                      </div>
                    </td>
                  </tr>
                ) : (
                  sortedProducts.map((product) => (
                    <tr key={product.id}>
                      <td>
                        {product.image_url ? (
                          <img src={product.image_url} alt={product.name} className="table-image" />
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
                      <td>{formatNumber(product.cost_price)}</td>
                      <td>{formatNumber(product.sell_price)}</td>
                      <td>
                        {stockLevelLoading ? <span className="skeleton skeleton-text" /> : stockMap.get(product.id) ?? 0}
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
      )}

      {createModalOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>
                {createModalTab === 'categories'
                  ? t('adminSections.createCategory')
                  : createModalTab === 'brands'
                    ? t('adminSections.createBrand')
                    : createModalTab === 'lines'
                      ? t('adminSections.createLine')
                      : t('adminSections.createProduct')}
              </h4>
              <button className="ghost" onClick={closeCreateModal}>
                {t('common.close')}
              </button>
            </div>
            {createModalTab === 'categories' && (
              <div className="form-stack">
                <p className="page-subtitle">{t('adminSections.createCategorySubtitle')}</p>
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
              </div>
            )}
            {createModalTab === 'brands' && (
              <div className="form-stack">
                <p className="page-subtitle">{t('adminSections.createBrandSubtitle')}</p>
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
              </div>
            )}
            {createModalTab === 'lines' && (
              <div className="form-stack">
                <p className="page-subtitle">{t('adminSections.createLineSubtitle')}</p>
                <div className="form-row">
                  <input
                    placeholder={t('admin.linePlaceholder')}
                    value={lineName}
                    onChange={(e) => setLineName(e.target.value)}
                  />
                  <select value={lineBrand} onChange={(e) => setLineBrand(e.target.value)}>
                    <option value="">{t('admin.brandSelect')}</option>
                    {sortedBrands.map((brand) => (
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
                {lineBrandMissing && (
                  <p className="page-subtitle">{t('admin.validation.selectBrandForLine')}</p>
                )}
              </div>
            )}
            {createModalTab === 'products' && (
              <div className="form-stack">
                <p className="page-subtitle">{t('adminSections.createProductSubtitle')}</p>
                <select
                  value={productCategoryId}
                  onChange={(e) => setProductCategoryId(e.target.value)}
                >
                  <option value="">{t('admin.categorySelect')}</option>
                  {sortedCategories.map((category) => (
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
            )}
          </div>
        </div>
      )}

      {editOpen && (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="modal-header">
              <h4>{t('common.edit', { defaultValue: 'Редактировать' })}</h4>
              <button className="ghost" onClick={closeEditModal}>
                {t('common.close')}
              </button>
            </div>
            <div className="form-stack">
              <input
                placeholder={t('admin.table.name')}
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
              {editType === 'products' && (
                <>
                  <div className="form-row">
                    <select
                      value={editCategoryId}
                      onChange={(e) => {
                        setEditCategoryId(e.target.value)
                        setEditBrandId('')
                        setEditLineId('')
                        setEditBrandLines([])
                      }}
                    >
                      <option value="">{t('admin.categorySelect')}</option>
                      {sortedCategories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                    <select
                      value={editBrandId}
                      onChange={(e) => {
                        setEditBrandId(e.target.value)
                        setEditLineId('')
                      }}
                      disabled={!editCategoryId}
                    >
                      <option value="">{t('admin.brandSelect')}</option>
                      {editCategoryBrands.map((brand) => (
                        <option key={brand.id} value={brand.id}>
                          {brand.name}
                        </option>
                      ))}
                    </select>
                    <select
                      value={editLineId}
                      onChange={(e) => setEditLineId(e.target.value)}
                      disabled={!editBrandId}
                    >
                      <option value="">{t('admin.lineSelect')}</option>
                      {editBrandLines.map((line) => (
                        <option key={line.id} value={line.id}>
                          {line.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-row">
                    <input
                      placeholder={t('admin.skuPlaceholder')}
                      value={editSku}
                      onChange={(e) => setEditSku(e.target.value)}
                    />
                    <input
                      placeholder={t('admin.barcodePlaceholder')}
                      value={editBarcode}
                      onChange={(e) => setEditBarcode(e.target.value)}
                    />
                  </div>
                  <div className="form-row">
                    <label className="form-field">
                      <span>{t('admin.unitLabel')}</span>
                      <select value={editUnit} onChange={(e) => setEditUnit(e.target.value)}>
                        <option value="pcs">{t('admin.unitPcs')}</option>
                        <option value="ml">{t('admin.unitMl')}</option>
                        <option value="g">{t('admin.unitG')}</option>
                      </select>
                    </label>
                    <label className="form-field">
                      <span>{t('admin.costPriceLabel')}</span>
                      <input
                        type="number"
                        min="0"
                        placeholder={t('admin.costPricePlaceholder')}
                        value={editCostPrice}
                        onChange={(e) => setEditCostPrice(e.target.value)}
                      />
                    </label>
                    <label className="form-field">
                      <span>{t('admin.sellPriceLabel')}</span>
                      <input
                        type="number"
                        min="0"
                        placeholder={t('admin.sellPricePlaceholder')}
                        value={editSellPrice}
                        onChange={(e) => setEditSellPrice(e.target.value)}
                      />
                    </label>
                  </div>
                  <div className="form-row">
                    <label className="form-field">
                      <span>{t('admin.productImageLabel')}</span>
                      <input
                        type="url"
                        placeholder={t('admin.productImagePlaceholder')}
                        value={editImageUrl}
                        onChange={(e) => setEditImageUrl(e.target.value)}
                      />
                    </label>
                    <label className="form-field">
                      <span>{t('admin.productImageUpload')}</span>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleEditImageUpload(e.target.files?.[0])}
                      />
                    </label>
                    {editImageUrl && (
                      <div className="image-preview">
                        <img src={editImageUrl} alt={t('admin.productImagePreview')} />
                        <button
                          type="button"
                          className="ghost"
                          onClick={() => setEditImageUrl('')}
                        >
                          {t('admin.clearImage')}
                        </button>
                      </div>
                    )}
                  </div>
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
                </>
              )}
              <div className="form-row">
                <button onClick={handleEditSave}>{t('common.save', { defaultValue: 'Сохранить' })}</button>
                <button className="ghost" onClick={closeEditModal}>
                  {t('common.close')}
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
                {t('common.close')}
              </button>
            </div>
            <div className="form-stack">
              <input
                placeholder={t('admin.searchBrandPlaceholder')}
                value={brandSearch}
                onChange={(e) => setBrandSearch(e.target.value)}
              />
              <div className="form-inline">
                <span className="muted">{t('admin.listRows')}</span>
                <button
                  type="button"
                  className={linkModalColumns === 1 ? '' : 'secondary'}
                  onClick={() => setLinkModalColumns(1)}
                >
                  1
                </button>
                <button
                  type="button"
                  className={linkModalColumns === 2 ? '' : 'secondary'}
                  onClick={() => setLinkModalColumns(2)}
                >
                  2
                </button>
              </div>
              <div className="modal-list-scroll">
                {filteredAvailableBrands.length === 0 ? (
                  <p className="page-subtitle">{t('admin.emptyAvailableBrands')}</p>
                ) : (
                  <div
                    className="form-row"
                    style={{ gridTemplateColumns: `repeat(${linkModalColumns}, minmax(0, 1fr))` }}
                  >
                    {filteredAvailableBrands.map((brand) => (
                      <div key={brand.id} className="card card-body">
                        <strong>{brand.name}</strong>
                        <button
                          onClick={() => linkBrandToCategory(brand.id)}
                          disabled={!categoryLinkId}
                        >
                          {t('admin.linkBrand')}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
