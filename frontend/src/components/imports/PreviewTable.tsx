import { useMemo, useState } from 'react'
import { PrimaryButton } from '../Buttons'
import type { ImportPreviewResponse } from '../../api/imports'

type PreviewTableProps = {
  preview: ImportPreviewResponse
  loading: boolean
  onRecalculate: (edits: Record<number, Record<string, string>>) => Promise<void>
}

export default function PreviewTable({ preview, loading, onRecalculate }: PreviewTableProps) {
  const [edits, setEdits] = useState<Record<number, Record<string, string>>>({})

  const columns = useMemo(() => {
    const first = preview.rows[0]
    return first ? Object.keys(first.values) : []
  }, [preview.rows])

  const setCell = (rowNumber: number, key: string, value: string) => {
    setEdits((prev) => ({
      ...prev,
      [rowNumber]: {
        ...(prev[rowNumber] ?? {}),
        [key]: value
      }
    }))
  }

  return (
    <div className="form-stack">
      <div className="form-row" style={{ justifyContent: 'space-between' }}>
        <h4>Предпросмотр</h4>
        <span className="page-subtitle">
          Всего: {preview.totals.total} • Валидно: {preview.totals.valid} • Ошибки: {preview.totals.invalid}
        </span>
      </div>
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>#</th>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
              <th>Ошибки</th>
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row) => (
              <tr key={row.row_number}>
                <td>{row.row_number}</td>
                {columns.map((column) => {
                  const cellValue = edits[row.row_number]?.[column] ?? row.values[column] ?? ''
                  const errors = row.errors.filter((error) => !error.column || error.column === column)
                  return (
                    <td key={`${row.row_number}-${column}`}>
                      <input
                        value={cellValue}
                        onChange={(e) => setCell(row.row_number, column, e.target.value)}
                        title={errors.map((error) => error.message).join('\n')}
                        style={errors.length > 0 ? { borderColor: '#b42318', background: '#fef3f2' } : undefined}
                      />
                    </td>
                  )
                })}
                <td title={row.errors.map((error) => error.message).join('\n')}>
                  {row.errors.length > 0 ? `Ошибок: ${row.errors.length}` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PrimaryButton type="button" onClick={() => onRecalculate(edits)} disabled={loading}>
        {loading ? 'Пересчитываем...' : 'Пересчитать preview'}
      </PrimaryButton>
    </div>
  )
}
