import { FormEvent, useEffect, useMemo, useState } from 'react'
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
  const [draftTitle, setDraftTitle] = useState('')
  const [draftSubtitle, setDraftSubtitle] = useState('')
  const [draftNote, setDraftNote] = useState('')
  const hasManagerSession = Boolean(localStorage.getItem('token'))

  const tenantSettingsQuery = useQuery({
    queryKey: ['tenantSettingsPublicCatalogEditor'],
    queryFn: async () => (await api.get<{ settings?: Record<string, unknown> }>('/tenant/settings')).data,
    enabled: hasManagerSession,
    retry: false
  })

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
  const internetCatalogSettings = useMemo(() => {
    const raw = tenantSettingsQuery.data?.settings?.internet_catalog
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {}
    return raw as Record<string, unknown>
  }, [tenantSettingsQuery.data])

  const catalogTitle =
    typeof internetCatalogSettings.title === 'string' && internetCatalogSettings.title.trim()
      ? internetCatalogSettings.title
      : t('admin.internetCatalogTitle', { defaultValue: 'Интернет-каталог' })
  const catalogSubtitle =
    typeof internetCatalogSettings.subtitle === 'string' && internetCatalogSettings.subtitle.trim()
      ? internetCatalogSettings.subtitle
      : t('admin.internetCatalogSubtitle', { defaultValue: 'Выберите товары и отправьте заказ в один клик.' })
  const catalogNote =
    typeof internetCatalogSettings.note === 'string' && internetCatalogSettings.note.trim()
      ? internetCatalogSettings.note
      : t('admin.internetCatalogNote', { defaultValue: 'Менеджер свяжется с вами для подтверждения.' })

  const saveCatalogContentMutation = useMutation({
    mutationFn: async () =>
      api.patch('/tenant/settings', {
        settings: {
          internet_catalog: {
            ...internetCatalogSettings,
            title: draftTitle.trim(),
            subtitle: draftSubtitle.trim(),
            note: draftNote.trim()
          }
        }
      }),
    onSuccess: async () => {
      await tenantSettingsQuery.refetch()
    }
  })
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

  useEffect(() => {
    setDraftTitle(catalogTitle)
    setDraftSubtitle(catalogSubtitle)
    setDraftNote(catalogNote)
  }, [catalogTitle, catalogSubtitle, catalogNote])

  return (
    <div className="page">
      <section className="catalog-hero card">
        <h2>{catalogTitle}</h2>
        <p className="page-subtitle">{catalogSubtitle}</p>
        <p className="catalog-hero__note">{catalogNote}</p>
      </section>

      {hasManagerSession && (
        <section className="card form-stack">
          <h3>{t('admin.catalogEditor', { defaultValue: 'Редактор страницы каталога' })}</h3>
          <p className="page-subtitle">
            {t('admin.catalogEditorHint', {
              defaultValue: 'Вы вошли как менеджер — можете менять заголовок и текст прямо на этой странице.'
            })}
          </p>
          <div className="form-row">
            <input value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} placeholder="Заголовок" />
            <input value={draftSubtitle} onChange={(e) => setDraftSubtitle(e.target.value)} placeholder="Подзаголовок" />
          </div>
          <input value={draftNote} onChange={(e) => setDraftNote(e.target.value)} placeholder="Доп. текст" />
          <button type="button" onClick={() => saveCatalogContentMutation.mutate()} disabled={saveCatalogContentMutation.isPending || tenantSettingsQuery.isLoading}>
            {saveCatalogContentMutation.isPending
              ? t('common.loading')
              : t('common.save', { defaultValue: 'Сохранить изменения' })}
          </button>
        </section>
      )}

      <div className="form-row">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t('admin.search', { defaultValue: 'Поиск товара' })} />
      </div>
      {isLoading && <p>{t('common.loading')}</p>}
      <div className="cards-grid catalog-grid">
        {groupedItems.map(([groupName, variants]) => {
          const selectedId = selectedVariants[groupName] ?? variants[0]?.id
          const selected = variants.find((item) => item.id === selectedId) ?? variants[0]
          if (!selected) return null
          return (
            <article key={groupName} className="card catalog-product-card">
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

      <form className="card catalog-order-card" onSubmit={submitOrder}>
        <h3>{t('common.order', { defaultValue: 'Оформление заказа' })}</h3>
        <input value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Имя" />
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Телефон" />
        <p>{Object.values(cart).reduce((acc, item) => acc + item.qty, 0)} шт.</p>
        <button type="submit" disabled={orderMutation.isPending || !Object.keys(cart).length}>Оформить</button>
      </form>
    </div>
  )
}
