// Typed API client — same-origin /api in production
import type {
  ForecastResponse,
  Freshness,
  KpiCard,
  MetricInfo,
  PipelineRun,
  ReportFull,
  ReportListItem,
  RecommendationResponse,
  Settings,
  UploadResponse,
} from './types'

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const detail = await safeDetail(res)
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const detail = await safeDetail(res)
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

async function safeDetail(res: Response): Promise<string> {
  try {
    const j = await res.json()
    return typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail ?? j)
  } catch {
    return `${res.status} ${res.statusText}`
  }
}

export const api = {
  health: () => get<{ status: string }>('/api/health'),
  kpis: () => get<KpiCard[]>('/api/kpis'),

  metrics: () => get<MetricInfo[]>('/api/metrics'),

  metricHistory: (metric: string, days = 180) =>
    get<{ date: string; value: number }[]>(`/api/metrics/${metric}/history?days=${days}`),

  forecast: (metric: string, days: number, sensitivity = 0.75, historyDays = 90) =>
    post<ForecastResponse>('/api/forecast', {
      metric,
      days,
      anomaly_sensitivity: sensitivity,
      include_history_days: historyDays,
    }),

  anomalies: (limit = 20, days = 90, sensitivity = 0.75) =>
    get<import('./types').AnomalyItem[]>(`/api/anomalies?limit=${limit}&days=${days}&sensitivity=${sensitivity}`),

  recommendations: () => get<RecommendationResponse>('/api/recommendations'),

  pipelineRuns: () => get<PipelineRun[]>('/api/pipeline/runs'),
  runPipeline: () => post<PipelineRun>('/api/pipeline/run'),
  freshness: () => get<Freshness>('/api/pipeline/freshness'),

  reports: () => get<ReportListItem[]>('/api/reports'),
  generateReport: (horizonDays: number) =>
    post<ReportFull>(`/api/reports/generate?horizon_days=${horizonDays}`),
  report: (id: number) => get<ReportFull>(`/api/reports/${id}`),
  reportMarkdownUrl: (id: number) => `${BASE}/api/reports/${id}/markdown`,

  settings: () => get<Settings>('/api/settings'),
  updateSettings: (patch: Partial<Settings>) =>
    fetch(`${BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }).then(async (r) => {
      if (!r.ok) throw new Error(await safeDetail(r))
      return r.json() as Promise<Settings>
    }),

  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData()
    form.append('file', file)
    form.append('source_format', 'auto')
    const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(await safeDetail(res))
    return res.json() as Promise<UploadResponse>
  },
}
