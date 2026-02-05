const rubCurrencyFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})

export const formatRubCurrency = (value: number | string | null | undefined) => {
  const normalized = typeof value === 'number' ? value : Number(value ?? 0)
  const safeValue = Number.isFinite(normalized) ? normalized : 0
  return rubCurrencyFormatter.format(safeValue).replace(/\u00a0/g, ' ')
}
