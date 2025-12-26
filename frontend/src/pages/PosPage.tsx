import { useEffect, useState } from 'react'
import api from '../api/client'

interface Product {
  id: string
  name: string
  price: number
}

interface SaleDetail {
  id: string
  status: string
  customer_name: string
  items: any[]
  payments: any[]
}

export default function PosPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [sale, setSale] = useState<SaleDetail | null>(null)
  const [customer, setCustomer] = useState('')
  const [selectedProduct, setSelectedProduct] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [paymentAmount, setPaymentAmount] = useState('0')
  const [provider, setProvider] = useState('cash')

  useEffect(() => {
    api.get('/products').then((res) => setProducts(res.data))
  }, [])

  const startSale = async () => {
    const res = await api.post('/pos/sales', { customer_name: customer })
    setSale({ ...res.data, items: [], payments: [] })
  }

  const addItem = async () => {
    if (!sale) return
    const product = products.find((p) => p.id === selectedProduct)
    if (!product) return
    const res = await api.post(`/pos/sales/${sale.id}/items`, {
      product_id: product.id,
      quantity: Number(quantity),
      unit_price: product.price,
      discount_amount: 0
    })
    setSale(res.data)
  }

  const addPayment = async () => {
    if (!sale) return
    const res = await api.post(`/pos/sales/${sale.id}/payments`, {
      amount: Number(paymentAmount),
      provider,
      reference: ''
    })
    setSale({ ...sale, payments: [...sale.payments, res.data] })
  }

  const finalize = async () => {
    if (!sale) return
    const res = await api.post(`/pos/sales/${sale.id}/finalize`)
    setSale({ ...sale, status: res.data.status })
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>POS</h2>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <input placeholder="Customer" value={customer} onChange={(e) => setCustomer(e.target.value)} />
          <button onClick={startSale}>Start Sale</button>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 8, marginTop: 12 }}>
            {products.map((p) => (
              <button key={p.id} onClick={() => setSelectedProduct(p.id)} style={{ padding: 12, border: selectedProduct === p.id ? '2px solid #2563eb' : '1px solid #cbd5e1' }}>
                <div>{p.name}</div>
                <div>${p.price}</div>
              </button>
            ))}
          </div>
        </div>
        <div style={{ width: 320, background: '#fff', padding: 12 }}>
          <h3>Cart</h3>
          {sale ? (
            <div>
              <p>Status: {sale.status}</p>
              <input placeholder="Qty" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
              <button onClick={addItem}>Add Item</button>
              <ul>
                {sale.items.map((item) => (
                  <li key={item.id}>
                    {item.product_id} x {item.quantity}
                  </li>
                ))}
              </ul>
              <h4>Payments</h4>
              <input placeholder="Amount" value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} />
              <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="external">External</option>
              </select>
              <button onClick={addPayment}>Add Payment</button>
              <ul>
                {sale.payments.map((p) => (
                  <li key={p.id}>
                    {p.provider}: {p.amount}
                  </li>
                ))}
              </ul>
              <button onClick={finalize}>Finalize</button>
            </div>
          ) : (
            <p>Start a sale to add items</p>
          )}
        </div>
      </div>
    </div>
  )
}
