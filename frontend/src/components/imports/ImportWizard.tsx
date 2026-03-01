import { useCallback, useMemo, useState } from 'react'
import FileUploader from './FileUploader'
import ColumnMapper from './ColumnMapper'
import PreviewTable from './PreviewTable'
import ImportStatus from './ImportStatus'
import {
  apply,
  downloadErrors,
  getImportById,
  getImports,
  preview,
  upload,
  type ImportHistoryItem,
  type ImportPreviewResponse,
  type ImportStatusResponse,
  type UploadImportResponse
} from '../../api/imports'
import { useToast } from '../ToastProvider'

type ImportWizardProps = {
  onClose: () => void
}

export default function ImportWizard({ onClose }: ImportWizardProps) {
  const { addToast } = useToast()
  const [step, setStep] = useState(0)
  const [uploadMeta, setUploadMeta] = useState<UploadImportResponse | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null)
  const [status, setStatus] = useState<ImportStatusResponse | null>(null)
  const [history, setHistory] = useState<ImportHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)

  const importId = uploadMeta?.import_id ?? previewData?.import_id ?? status?.id

  const loadHistory = useCallback(async () => {
    try {
      const res = await getImports()
      setHistory(res)
    } catch {
      addToast('Не удалось загрузить историю импортов', 'error')
    }
  }, [addToast])

  const handleUpload = async (params: { file: File; sheet?: string; options: Record<string, unknown> }) => {
    setLoading(true)
    try {
      const res = await upload(params)
      setUploadMeta(res)
      setStep(1)
      await loadHistory()
    } catch {
      addToast('Ошибка загрузки файла', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleBuildPreview = async (nextMapping: Record<string, string>) => {
    if (!uploadMeta?.import_id) return
    setLoading(true)
    try {
      const res = await preview({ import_id: uploadMeta.import_id, mapping: nextMapping })
      setMapping(nextMapping)
      setPreviewData(res)
      setStep(2)
    } catch {
      addToast('Ошибка построения preview', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRecalculate = async (edits: Record<number, Record<string, string>>) => {
    if (!importId) return
    setLoading(true)
    try {
      const res = await preview({ import_id: importId, mapping, edits })
      setPreviewData(res)
    } catch {
      addToast('Не удалось пересчитать preview', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleApply = async (dryRun: boolean, background: boolean) => {
    if (!importId) return
    setApplying(true)
    try {
      const res = await apply({
        import_id: importId,
        mode: background ? 'background' : 'sync',
        mapping,
        options: { dry_run: dryRun }
      })
      setStatus(res)
      setStep(3)
      await loadHistory()
    } catch {
      addToast('Ошибка запуска импорта', 'error')
    } finally {
      setApplying(false)
    }
  }

  const handlePoll = useCallback(async () => {
    if (!importId) return
    try {
      const res = await getImportById(importId)
      setStatus(res)
      if (['done', 'failed'].includes(res.status)) {
        await loadHistory()
      }
    } catch {
      addToast('Ошибка обновления статуса импорта', 'error')
    }
  }, [addToast, importId, loadHistory])

  const handleDownloadErrors = async () => {
    if (!importId) return
    try {
      const blob = await downloadErrors(importId)
      const href = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = href
      link.download = `import-errors-${importId}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(href)
    } catch {
      addToast('Не удалось скачать ошибки', 'error')
    }
  }

  const stepTitle = useMemo(() => ['Файл', 'Маппинг', 'Preview', 'Статус'][step] ?? 'Импорт', [step])

  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ width: 'min(1100px, 95vw)' }}>
        <div className="modal-header">
          <h4>Импорт каталога — {stepTitle}</h4>
          <button className="ghost" onClick={onClose}>
            Закрыть
          </button>
        </div>

        {step === 0 && <FileUploader onUpload={handleUpload} loading={loading} />}
        {step === 1 && uploadMeta && (
          <ColumnMapper columns={uploadMeta.columns} onSubmit={handleBuildPreview} loading={loading} />
        )}
        {step === 2 && previewData && (
          <div className="form-stack">
            <PreviewTable preview={previewData} onRecalculate={handleRecalculate} loading={loading} />
            <div className="form-row" style={{ justifyContent: 'space-between' }}>
              <button className="secondary" onClick={() => setStep(1)}>
                Назад к маппингу
              </button>
              <button onClick={() => setStep(3)}>Далее: запуск</button>
            </div>
          </div>
        )}
        {step === 3 && (
          <ImportStatus
            status={status}
            history={history}
            loading={loading}
            applying={applying}
            onApply={handleApply}
            onPoll={handlePoll}
            onDownloadErrors={handleDownloadErrors}
          />
        )}
      </div>
    </div>
  )
}
