import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'

type PaymentMethod = 'cash' | 'card' | 'external'

interface Product {
  id: string
  name: string
  price: number
}

interface CartItem {
  product: Product
  qty: number
}

interface PaymentDraft {
  amount: number
  method: PaymentMethod
  reference: string
}

interface SaleItem {
  id: string
  product_id: string
  qty: number
  unit_price: number
  line_total: number
}

interface PaymentRecord {
  id: string
  amount: number
  method: PaymentMethod
  status: string
  reference: string
}

interface SaleDetail {
  id: string
  status: string
  total_amount: number
  currency: string
  items: SaleItem[]
  payments: PaymentRecord[]
}

export default function PosPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [payments, setPayments] = useState<PaymentDraft[]>([])
  const [search, setSearch] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('0')
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('cash')
  const [paymentReference, setPaymentReference] = useState('')
  const [sale, setSale] = useState<SaleDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/products').then((res) => setProducts(res.data))
  }, [])

  const filteredProducts = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return products
    return products.filter((product) => product.name.toLowerCase().includes(query))
  }, [products, search])

  const subtotal = useMemo(() => {
    return cartItems.reduce((sum, item) => sum + item.qty * item.product.price, 0)
  }, [cartItems])

  const paidTotal = useMemo(() => {
    return payments.reduce((sum, payment) => sum + payment.amount, 0)
  }, [payments])

  const totalDue = Math.max(subtotal - paidTotal, 0)

  const addToCart = (product: Product) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.product.id === product.id)
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, qty: item.qty + 1 } : item
        )
      }
      return [...prev, { product, qty: 1 }]
    })
  }

  const updateQty = (productId: string, qty: number) => {
    if (Number.isNaN(qty) || qty <= 0) return
    setCartItems((prev) => prev.map((item) => (item.product.id === productId ? { ...item, qty } : item)))
  }

  const removeItem = (productId: string) => {
    setCartItems((prev) => prev.filter((item) => item.product.id !== productId))
  }

  const addPayment = () => {
    const amountValue = Number(paymentAmount)
    if (!amountValue || amountValue <= 0) return
    setPayments((prev) => [...prev, { amount: amountValue, method: paymentMethod, reference: paymentReference }])
    setPaymentAmount('0')
    setPaymentReference('')
  }

  const removePayment = (index: number) => {
    setPayments((prev) => prev.filter((_, idx) => idx !== index))
  }

  const finalizeSale = async () => {
    setError('')
    if (cartItems.length === 0) {
      setError('Add items to the cart before finalizing.')
      return
    }
    const payload = {
      items: cartItems.map((item) => ({
        product_id: item.product.id,
        qty: item.qty,
        unit_price: item.product.price
      })),
      payments: payments.map((payment) => ({
        amount: payment.amount,
        method: payment.method,
        reference: payment.reference
      }))
    }
    try {
      const res = await api.post('/sales', payload)
      setSale(res.data)
      setCartItems([])
      setPayments([])
    } catch (e) {
      setError('Unable to finalize sale.')
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h2>POS</h2>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          <input placeholder="Search products" value={search} onChange={(e) => setSearch(e.target.value)} />
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: 8,
              marginTop: 12
            }}
          >
            {filteredProducts.map((product) => (
              <button
                key={product.id}
                onClick={() => addToCart(product)}
                style={{ padding: 12, border: '1px solid #cbd5e1', background: '#fff' }}
              >
                <div>{product.name}</div>
                <div>${product.price}</div>
              </button>
            ))}
          </div>
        </div>
        <div style={{ width: 360, background: '#fff', padding: 12 }}>
          <h3>Cart</h3>
          {cartItems.length === 0 ? (
            <p>No items in cart</p>
          ) : (
            <div>
              <ul>
                {cartItems.map((item) => (
                  <li key={item.product.id} style={{ marginBottom: 8 }}>
                    <div>{item.product.name}</div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        value={item.qty}
                        onChange={(e) => updateQty(item.product.id, Number(e.target.value))}
                        style={{ width: 60 }}
                      />
                      <span>${(item.qty * item.product.price).toFixed(2)}</span>
                      <button onClick={() => removeItem(item.product.id)}>Remove</button>
                    </div>
                  </li>
                ))}
              </ul>
              <p>Subtotal: ${subtotal.toFixed(2)}</p>
            </div>
          )}
          <h4>Payments</h4>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              placeholder="Amount"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
              style={{ width: 80 }}
            />
            <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}>
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="external">External</option>
            </select>
            <input
              placeholder="Reference"
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
              style={{ flex: 1 }}
            />
            <button onClick={addPayment}>Add</button>
          </div>
          <ul>
            {payments.map((payment, index) => (
              <li key={`${payment.method}-${index}`}>
                {payment.method} ${payment.amount.toFixed(2)}
                {payment.reference ? ` (${payment.reference})` : ''}
                <button onClick={() => removePayment(index)} style={{ marginLeft: 8 }}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
          <p>Due: ${totalDue.toFixed(2)}</p>
          <button onClick={finalizeSale} style={{ marginTop: 12 }}>
            Finalize Sale
          </button>
          {error && <p style={{ color: 'red' }}>{error}</p>}
          {sale && (
            <div style={{ marginTop: 12 }}>
              <p>Sale {sale.id}</p>
              <p>Status: {sale.status}</p>
              <p>Total: ${sale.total_amount}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
