import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import api from '../api/client'

type PublicProduct = {
  id: string
  name: string
  sku?: string | null
  image_url?: string | null
  unit: string
  sell_price: number
  category: string
  brand: string
  line?: string | null
  on_hand: number
  variant_group?: string | null
  variant_name?: string | null
}

type CartItem = { product: PublicProduct; qty: number }

export default function PublicCatalogPage() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>({})
  const [cart, setCart] = useState<Record<string, CartItem>>({})
  const [customerName, setCustomerName] = useState('')
  const [phone, setPhone] = useState('')

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['publicCatalog', query],
    queryFn: async () => (await api.get<{ items: PublicProduct[] }>('/public/catalog/products', { params: { q: query || undefined } })).data
  })

  const orderMutation = useMutation({
    mutationFn: async () =>
      api.post('/public/catalog/orders', {
        customer_name: customerName,
        phone,
        items: Object.values(cart).map((item) => ({ product_id: item.product.id, qty: item.qty }))
      }),
    onSuccess: () => {
      setCart({})
      setCustomerName('')
      setPhone('')
      void refetch()
    }
  })

  const items = useMemo(() => data?.items ?? [], [data])
  const groupedItems = useMemo(() => {
    const map = new Map<string, PublicProduct[]>()
    for (const item of items) {
      const key = item.variant_group?.trim() || item.name
      const list = map.get(key) ?? []
      list.push(item)
      map.set(key, list)
    }
    return Array.from(map.entries())
  }, [items])

  const addToCart = (product: PublicProduct) => {
    setCart((prev) => ({
      ...prev,
      [product.id]: { product, qty: (prev[product.id]?.qty ?? 0) + 1 }
    }))
  }

  const submitOrder = (event: FormEvent) => {
    event.preventDefault()
    if (!customerName.trim() || !phone.trim() || Object.keys(cart).length === 0) return
    orderMutation.mutate()
  }

  return (
    <div className="page">
      <h2>{t('admin.internetCatalogTitle', { defaultValue: 'Интернет-каталог' })}</h2>
      <div className="form-row" style={{ marginBottom: 12 }}>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t('admin.search', { defaultValue: 'Поиск товара' })} />
      </div>
      {isLoading && <p>{t('common.loading')}</p>}
      <div className="cards-grid">
        {groupedItems.map(([groupName, variants]) => {
          const selectedId = selectedVariants[groupName] ?? variants[0]?.id
          const selected = variants.find((item) => item.id === selectedId) ?? variants[0]
          if (!selected) return null
          return (
            <article key={groupName} className="card">
              {selected.image_url ? <img src={selected.image_url} alt={selected.name} className="table-image" /> : null}
              <h4>{groupName}</h4>
              {variants.length > 1 && (
                <select value={selected.id} onChange={(e) => setSelectedVariants((prev) => ({ ...prev, [groupName]: e.target.value }))}>
                  {variants.map((variant) => (
                    <option key={variant.id} value={variant.id}>
                      {variant.variant_name || variant.name}
                    </option>
                  ))}
                </select>
              )}
              <div>{selected.brand} · {selected.category}</div>
              <div>{t('adminStock.onHand', { defaultValue: 'On hand' })}: {selected.on_hand}</div>
              <strong>{selected.sell_price}</strong>
              <button type="button" onClick={() => addToCart(selected)}>
                {t('common.add', { defaultValue: 'Добавить' })}
              </button>
            </article>
          )
        })}
      </div>

      <form className="card" onSubmit={submitOrder} style={{ marginTop: 16 }}>
        <h3>{t('common.order', { defaultValue: 'Оформление заказа' })}</h3>
        <input value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Имя" />
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Телефон" />
        <p>{Object.values(cart).reduce((acc, item) => acc + item.qty, 0)} шт.</p>
        <button type="submit" disabled={orderMutation.isPending || !Object.keys(cart).length}>Оформить</button>
      </form>
    </div>
  )
}
