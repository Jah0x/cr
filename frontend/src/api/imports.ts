import api from './client'

export type ImportJobStatus = 'queued' | 'running' | 'done' | 'failed'

export type UploadImportResponse = {
  import_id: string
  file_name?: string
  sheet_name?: string
  columns: string[]
  options?: Record<string, unknown>
}

export type ImportPreviewRowError = {
  column?: string
  message: string
}

export type ImportPreviewRow = {
  row_number: number
  values: Record<string, string>
  errors: ImportPreviewRowError[]
}

export type ImportPreviewResponse = {
  import_id: string
  rows: ImportPreviewRow[]
  totals: {
    total: number
    valid: number
    invalid: number
  }
}

export type ImportCounters = {
  created: number
  updated: number
  failed: number
}

export type ImportStatusResponse = {
  id: string
  status: ImportJobStatus
  processed: number
  total: number
  counters: ImportCounters
  error_message?: string
  started_at?: string
  finished_at?: string
}

export type ImportHistoryItem = {
  id: string
  file_name?: string
  status: ImportJobStatus
  created_at: string
  counters: ImportCounters
}

export async function upload(params: {
  file: File
  sheet?: string
  options?: Record<string, unknown>
}) {
  const formData = new FormData()
  formData.append('file', params.file)
  if (params.sheet) {
    formData.append('sheet', params.sheet)
  }
  if (params.options) {
    formData.append('options', JSON.stringify(params.options))
  }

  const res = await api.post<UploadImportResponse>('/imports/upload', formData)
  return res.data
}

export async function preview(payload: {
  import_id: string
  mapping: Record<string, string>
  edits?: Record<number, Record<string, string>>
  options?: Record<string, unknown>
}) {
  const res = await api.post<ImportPreviewResponse>('/imports/preview', payload)
  return res.data
}

export async function apply(payload: { import_id: string; dry_run?: boolean; background?: boolean }) {
  const res = await api.post<ImportStatusResponse>(`/imports/${payload.import_id}/apply`, payload)
  return res.data
}

export async function getImports() {
  const res = await api.get<ImportHistoryItem[]>('/imports')
  return res.data
}

export async function getImportById(importId: string) {
  const res = await api.get<ImportStatusResponse>(`/imports/${importId}`)
  return res.data
}

export async function downloadErrors(importId: string) {
  const res = await api.get<Blob>(`/imports/${importId}/errors`, { responseType: 'blob' })
  return res.data
}
