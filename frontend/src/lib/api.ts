import { env } from './env'
import { getAccessToken } from './supabase'
import { http } from './http'

// ── Types ──────────────────────────────────────────────────────────────────

export interface Project {
  id: string
  name: string
  status: 'collecting' | 'reviewing' | 'complete'
  user_id: string
  created_at: string
}

export interface Document {
  id: string
  project_id: string
  filename: string
  storage_path: string | null
  converted_path: string | null
  mime_type: string | null
  status: 'uploading' | 'chunking' | 'embedded' | 'ready' | 'error'
}

export interface GapFlag {
  id: string
  project_id: string
  field_name: string
  flag_type: 'gap' | 'conflict' | 'missing'
  description: string
  resolved: boolean
}

export interface AnalysisOutput {
  id: string
  project_id: string
  script_name: string
  output_path: string
  status: 'running' | 'complete' | 'error'
  created_at: string
}

export interface SchemaField {
  name: string
  description: string
  required?: boolean
  expected_type?: string
}

export interface DDSchema {
  id: string
  project_id: string
  fields: SchemaField[]
}

export interface ReportCitation {
  citation_id: string
  filename: string
  chunk_index: number
  chunk_id?: string | null
  document_id?: string | null
  label: string
}

export interface ReportDetail extends AnalysisOutput {
  report_text: string
  citations: ReportCitation[]
}

export interface EvidenceChunk {
  id: string
  document_id: string
  project_id: string
  filename: string
  chunk_index: number
  content: string
}

export interface ReportCitationLookup {
  report_id: string
  citation: ReportCitation
  chunks: EvidenceChunk[]
}

// ── Projects ───────────────────────────────────────────────────────────────

export const listProjects = () => http.get<Project[]>('/api/projects/')
export const createProject = (name: string) => http.post<Project>('/api/projects/', { name })
export const deleteProject = (id: string) => http.delete<void>(`/api/projects/${id}`)

// ── Documents ──────────────────────────────────────────────────────────────

export const listDocuments = (projectId: string) =>
  http.get<Document[]>(`/api/documents/${projectId}`)

export const uploadDocument = async (projectId: string, file: File): Promise<Document> => {
  const token = await getAccessToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const formData = new FormData()
  formData.append('project_id', projectId)
  formData.append('file', file)

  const res = await fetch(`${env.apiBaseUrl}/api/documents/upload`, {
    method: 'POST',
    headers,
    body: formData,
  })
  if (!res.ok) throw new Error('Upload failed')
  return res.json() as Promise<Document>
}

export const getDocumentStatus = (documentId: string) =>
  http.get<{ document_id: string; status: Document['status'] }>(`/api/documents/${documentId}/status`)

// ── Gap flags ──────────────────────────────────────────────────────────────

export const listGapFlags = (projectId: string) =>
  http.get<GapFlag[]>(`/api/gaps/${projectId}`)

export const resolveGapFlag = (gapId: string) =>
  http.patch<GapFlag>(`/api/gaps/${gapId}/resolve`)

// ── Analysis outputs ───────────────────────────────────────────────────────

export const listAnalysisOutputs = (projectId: string) =>
  http.get<AnalysisOutput[]>(`/api/analysis/${projectId}`)

export const downloadAnalysisOutput = async (outputId: string): Promise<void> => {
  const token = await getAccessToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${env.apiBaseUrl}/api/analysis/${outputId}/download`, {
    headers,
  })
  if (!res.ok) {
    throw new Error(`Download failed: ${res.status}`)
  }

  const blob = await res.blob()
  const disposition = res.headers.get('content-disposition') ?? ''
  const match = disposition.match(/filename="?([^"]+)"?/i)
  const filename = match?.[1] ?? 'analysis-output'

  const url = URL.createObjectURL(blob)
  try {
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    anchor.rel = 'noopener noreferrer'
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  } finally {
    URL.revokeObjectURL(url)
  }
}

// ── Schema / Reports ──────────────────────────────────────────────────────

export const getSchema = (projectId: string) =>
  http.get<DDSchema>(`/api/schema/${projectId}`)

export const createReport = (projectId: string) =>
  http.post<ReportDetail>(`/api/projects/${projectId}/reports`)

export const getReport = (reportId: string) =>
  http.get<ReportDetail>(`/api/reports/${reportId}`)

export const getReportCitation = (reportId: string, citationId: string) =>
  http.get<ReportCitationLookup>(`/api/reports/${reportId}/citations/${citationId}`)

// ── Templates ─────────────────────────────────────────────────────────────

export const getTemplate = (projectId: string) =>
  http.get<{ project_id: string; content: string }>(`/api/template/${projectId}`)

export const updateTemplate = (projectId: string, content: string) =>
  http.put<{ project_id: string; content: string }>(`/api/template/${projectId}`, { content })
