import { useEffect, useState } from 'react'
import api from '../../api/client'

type Product = {
  id: string
  name: string
  variant_group?: string | null
  variant_name?: string | null
  is_hidden: boolean
}

export default function AdminCatalogVisibilityPage() {
  const [items, setItems] = useState<Product[]>([])

  const load = async () => {
    const res = await api.get<Product[]>('/products', { params: { is_active: true } })
    setItems(res.data)
  }

  useEffect(() => {
    void load()
  }, [])

  const toggle = async (item: Product) => {
    await api.patch(`/products/${item.id}`, { is_hidden: !item.is_hidden })
    await load()
  }

  return (
    <div className="page">
      <h2>Управление ассортиментом</h2>
      <table className="table">
        <thead>
          <tr><th>Товар</th><th>Вариант</th><th>Скрыт</th></tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.variant_group || item.name}</td>
              <td>{item.variant_name || '-'}</td>
              <td><input type="checkbox" checked={item.is_hidden} onChange={() => toggle(item)} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
