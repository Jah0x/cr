import { useEffect } from 'react'
import { PrimaryButton } from '../Buttons'
import type { ImportHistoryItem, ImportStatusResponse } from '../../api/imports'

type ImportStatusProps = {
  status: ImportStatusResponse | null
  history: ImportHistoryItem[]
  loading: boolean
  applying: boolean
  onApply: (dryRun: boolean, background: boolean) => Promise<void>
  onPoll: () => Promise<void>
  onDownloadErrors: () => Promise<void>
}

export default function ImportStatus({
  status,
  history,
  loading,
  applying,
  onApply,
  onPoll,
  onDownloadErrors
}: ImportStatusProps) {
  useEffect(() => {
    if (!status) return
    if (!['queued', 'running'].includes(status.status)) return

    const timer = setInterval(() => {
      void onPoll()
    }, 2000)

    return () => clearInterval(timer)
  }, [status, onPoll])

  return (
    <div className="form-stack">
      <h4>Импорт</h4>
      <div className="form-row">
        <PrimaryButton type="button" onClick={() => onApply(true, false)} disabled={loading || applying}>
          Dry-run
        </PrimaryButton>
        <PrimaryButton type="button" onClick={() => onApply(false, true)} disabled={loading || applying}>
          Применить в фоне
        </PrimaryButton>
        <button className="secondary" onClick={onDownloadErrors} disabled={!status || status.counters.failed === 0}>
          Скачать ошибки
        </button>
      </div>

      {status && (
        <div className="card">
          <p>
            Статус: <strong>{status.status}</strong>
          </p>
          <p>
            Прогресс: {status.processed}/{status.total}
          </p>
          <p>
            Создано: {status.counters.created} • Обновлено: {status.counters.updated} • Ошибки: {status.counters.failed}
          </p>
          {status.error_message && <p style={{ color: '#b42318' }}>{status.error_message}</p>}
        </div>
      )}

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Дата</th>
              <th>Статус</th>
              <th>Итог</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.created_at ? new Date(item.created_at).toLocaleString() : '—'}</td>
                <td>{item.status}</td>
                <td>
                  +{item.counters.created} / ~{item.counters.updated} / !{item.counters.failed}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
