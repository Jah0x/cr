import { useEffect, useState } from 'react'
import api from '../api/client'

type Category = { id: string; name: string }
type Brand = { id: string; name: string }
type ProductLine = { id: string; name: string; brand_id: string }
type Product = { id: string; name: string; price: number }
type Supplier = { id: string; name: string }

export default function AdminDashboard() {
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

  return (
    <div style={{ padding: 24 }}>
      <h2>Admin</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>Catalog</h3>
          <input placeholder="Category" value={categoryName} onChange={(e) => setCategoryName(e.target.value)} />
          <button onClick={createCategory}>Add Category</button>
          <input placeholder="Brand" value={brandName} onChange={(e) => setBrandName(e.target.value)} />
          <button onClick={createBrand}>Add Brand</button>
          <input placeholder="Line" value={lineName} onChange={(e) => setLineName(e.target.value)} />
          <select value={lineBrand} onChange={(e) => setLineBrand(e.target.value)}>
            <option value="">Brand</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
          <button onClick={createLine}>Add Line</button>
          <input placeholder="SKU" value={productSku} onChange={(e) => setProductSku(e.target.value)} />
          <input placeholder="Product" value={productName} onChange={(e) => setProductName(e.target.value)} />
          <input placeholder="Price" value={productPrice} onChange={(e) => setProductPrice(e.target.value)} />
          <button onClick={createProduct}>Add Product</button>
          <ul>
            {products.map((p) => (
              <li key={p.id}>{p.name}</li>
            ))}
          </ul>
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>Suppliers & Purchasing</h3>
          <input placeholder="Supplier" value={supplierName} onChange={(e) => setSupplierName(e.target.value)} />
          <button onClick={createSupplier}>Add Supplier</button>
          <button onClick={createInvoice}>New Invoice</button>
          {invoiceId && <p>Working invoice {invoiceId}</p>}
          <select value={purchaseProduct} onChange={(e) => setPurchaseProduct(e.target.value)}>
            <option value="">Product</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input placeholder="Qty" value={purchaseQty} onChange={(e) => setPurchaseQty(e.target.value)} />
          <input placeholder="Cost" value={purchaseCost} onChange={(e) => setPurchaseCost(e.target.value)} />
          <button onClick={addPurchaseItem}>Add Item</button>
          <button onClick={postInvoice}>Post Invoice</button>
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>Stock</h3>
          <select value={stockProduct} onChange={(e) => setStockProduct(e.target.value)}>
            <option value="">Product</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input placeholder="Qty" value={stockQty} onChange={(e) => setStockQty(e.target.value)} />
          <button onClick={adjustStock}>Adjust</button>
          <h4>Stock Levels</h4>
          <ul>
            {products.map((p) => (
              <li key={p.id}>{p.name}</li>
            ))}
          </ul>
        </div>
        <div style={{ background: '#fff', padding: 12 }}>
          <h3>Reports</h3>
          <button onClick={loadReports}>Load Summary</button>
          {reports && (
            <div>
              <p>Total sales: {reports.total_sales}</p>
              <p>Total purchases: {reports.total_purchases}</p>
              <p>Gross margin: {reports.gross_margin}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
