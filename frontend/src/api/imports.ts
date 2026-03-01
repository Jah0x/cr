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
  created_at?: string
  counters: ImportCounters
}

type BackendImportOut = {
  id: string
  filename: string
  status: ImportJobStatus
  rows_total: number
  rows_valid: number
  rows_invalid: number
  counters?: Partial<ImportCounters>
}

const parseCsvColumns = async (file: File, delimiter = ','): Promise<string[]> => {
  const text = await file.text()
  const [header = ''] = text.split(/\r?\n/, 1)
  return header
    .split(delimiter)
    .map((value) => value.trim())
    .filter(Boolean)
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
  if (params.sheet) {
    formData.append('sheet_name', params.sheet)
  }
  if (typeof params.options?.delimiter === 'string') {
    formData.append('delimiter', params.options.delimiter)
  }

  const res = await api.post<BackendImportOut>('/admin/imports/catalog/upload', formData)
  const columns = await parseCsvColumns(params.file, String(params.options?.delimiter ?? ','))
  return {
    import_id: res.data.id,
    file_name: res.data.filename,
    columns,
    options: params.options
  }
}

export async function preview(payload: {
  import_id: string
  mapping: Record<string, string>
  edits?: Record<number, Record<string, string>>
  options?: Record<string, unknown>
}) {
  const res = await api.post<{
    rows: Record<string, string>[]
    summary: { rows: number; valid: number; invalid: number }
    sample_actions: Array<{ row: number; action: string; reason: string | null }>
  }>('/admin/imports/catalog/preview', payload)

  const errorByRow = new Map<number, string[]>()
  for (const action of res.data.sample_actions) {
    if (action.action !== 'error' || !action.reason) continue
    const current = errorByRow.get(action.row) ?? []
    current.push(action.reason)
    errorByRow.set(action.row, current)
  }

  return {
    import_id: payload.import_id,
    rows: res.data.rows.map((values, index) => ({
      row_number: index + 2,
      values,
      errors: (errorByRow.get(index + 2) ?? []).map((message) => ({ message }))
    })),
    totals: {
      total: res.data.summary.rows,
      valid: res.data.summary.valid,
      invalid: res.data.summary.invalid
    }
  }
}

export async function apply(payload: {
  import_id: string
  mode: 'sync' | 'background'
  mapping: Record<string, string>
  options?: Record<string, unknown>
}) {
  const res = await api.post<{
    import_id: string
    status: ImportJobStatus
    counters: Partial<ImportCounters>
  }>('/admin/imports/catalog/apply', payload)
  return {
    id: res.data.import_id,
    status: res.data.status,
    processed: res.data.counters.processed ?? 0,
    total: res.data.counters.total ?? 0,
    counters: {
      created: res.data.counters.created ?? 0,
      updated: res.data.counters.updated ?? 0,
      failed: res.data.counters.failed ?? 0
    }
  }
}

export async function getImports() {
  const res = await api.get<BackendImportOut[]>('/admin/imports')
  return res.data.map((item) => ({
    id: item.id,
    file_name: item.filename,
    status: item.status,
    counters: {
      created: item.counters?.created ?? item.rows_valid,
      updated: item.counters?.updated ?? 0,
      failed: item.counters?.failed ?? item.rows_invalid
    }
  }))
}

export async function getImportById(importId: string) {
  const res = await api.get<BackendImportOut>(`/admin/imports/${importId}`)
  return {
    id: res.data.id,
    status: res.data.status,
    processed: res.data.rows_valid,
    total: res.data.rows_total,
    counters: {
      created: res.data.counters?.created ?? res.data.rows_valid,
      updated: res.data.counters?.updated ?? 0,
      failed: res.data.counters?.failed ?? res.data.rows_invalid
    }
  }
}

export async function downloadErrors(importId: string) {
  const res = await api.get<Blob>(`/admin/imports/${importId}/errors`, { responseType: 'blob' })
  return res.data
}
