import { useState } from 'react'
import { PrimaryButton } from '../Buttons'

type FileUploaderProps = {
  onUpload: (params: { file: File; sheet?: string; options: Record<string, unknown> }) => Promise<void>
  loading: boolean
}

export default function FileUploader({ onUpload, loading }: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [sheet, setSheet] = useState('')
  const [skipHeader, setSkipHeader] = useState(true)
  const [delimiter, setDelimiter] = useState(',')

  const submit = async () => {
    if (!file) return
    await onUpload({
      file,
      sheet: sheet.trim() || undefined,
      options: { skip_header: skipHeader, delimiter }
    })
  }

  return (
    <div className="form-stack">
      <h4>Загрузка файла</h4>
      <label className="form-field">
        <span>Файл (CSV/XLSX)</span>
        <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      <div className="form-row">
        <label className="form-field">
          <span>Лист (опционально)</span>
          <input value={sheet} onChange={(e) => setSheet(e.target.value)} placeholder="Sheet1" />
        </label>
        <label className="form-field">
          <span>Разделитель</span>
          <input value={delimiter} onChange={(e) => setDelimiter(e.target.value || ',')} maxLength={1} />
        </label>
      </div>
      <label className="form-row" style={{ alignItems: 'center', gap: 8 }}>
        <input type="checkbox" checked={skipHeader} onChange={(e) => setSkipHeader(e.target.checked)} />
        <span>Первая строка — заголовок</span>
      </label>
      <PrimaryButton type="button" onClick={submit} disabled={!file || loading}>
        {loading ? 'Загружаем...' : 'Загрузить'}
      </PrimaryButton>
    </div>
  )
}
