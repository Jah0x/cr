import { useMemo, useState } from 'react'
import { PrimaryButton } from '../Buttons'

type ColumnMapperProps = {
  columns: string[]
  loading: boolean
  onSubmit: (mapping: Record<string, string>) => Promise<void>
}

const TARGET_FIELDS = [
  { key: 'name', label: 'Название' },
  { key: 'sku', label: 'SKU' },
  { key: 'barcode', label: 'Штрихкод' },
  { key: 'category', label: 'Категория' },
  { key: 'brand', label: 'Бренд' },
  { key: 'line', label: 'Линейка' },
  { key: 'cost_price', label: 'Себестоимость' },
  { key: 'sell_price', label: 'Цена продажи' }
]

export default function ColumnMapper({ columns, loading, onSubmit }: ColumnMapperProps) {
  const initialMap = useMemo(
    () =>
      TARGET_FIELDS.reduce<Record<string, string>>((acc, field) => {
        const auto = columns.find((column) => column.toLowerCase().includes(field.key))
        acc[field.key] = auto ?? ''
        return acc
      }, {}),
    [columns]
  )

  const [mapping, setMapping] = useState<Record<string, string>>(initialMap)

  const handleSubmit = async () => {
    await onSubmit(mapping)
  }

  return (
    <div className="form-stack">
      <h4>Маппинг колонок</h4>
      {TARGET_FIELDS.map((field) => (
        <label className="form-field" key={field.key}>
          <span>{field.label}</span>
          <select
            value={mapping[field.key] ?? ''}
            onChange={(e) => setMapping((prev) => ({ ...prev, [field.key]: e.target.value }))}
          >
            <option value="">Не сопоставлено</option>
            {columns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </label>
      ))}
      <PrimaryButton type="button" onClick={handleSubmit} disabled={loading}>
        {loading ? 'Строим preview...' : 'Продолжить'}
      </PrimaryButton>
    </div>
  )
}
