import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
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
}

export default function PublicCatalogPage() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['publicCatalog', query],
    queryFn: async () => (await api.get<{ items: PublicProduct[] }>('/public/catalog/products', { params: { q: query || undefined } })).data
  })

  const items = useMemo(() => data?.items ?? [], [data])

  return (
    <div className="page">
      <h2>{t('admin.internetCatalogTitle', { defaultValue: 'Интернет-каталог' })}</h2>
      <div className="form-row" style={{ marginBottom: 12 }}>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t('admin.search', { defaultValue: 'Поиск товара' })} />
      </div>
      {isLoading && <p>{t('common.loading')}</p>}
      <div className="cards-grid">
        {items.map((item) => (
          <article key={item.id} className="card">
            {item.image_url ? <img src={item.image_url} alt={item.name} className="table-image" /> : null}
            <h4>{item.name}</h4>
            <div>{item.brand} · {item.category}</div>
            <div>{t('adminStock.onHand', { defaultValue: 'On hand' })}: {item.on_hand}</div>
            <strong>{item.sell_price}</strong>
          </article>
        ))}
      </div>
    </div>
  )
}
