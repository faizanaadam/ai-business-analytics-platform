// Shared API types

export type Unit = 'currency' | 'percent' | 'count'

export interface KpiCard {
  key: string
  label: string
  value: number
  unit: Unit
  trend_pct: number
  direction: 'up' | 'down' | 'flat'
  good_direction: 'up' | 'down'
}

export interface HistoryPoint {
  date: string
  value: number
  anomaly?: boolean
}

export interface ForecastPoint {
  date: string
  value: number
  lower95: number
  upper95: number
  lower80: number
  upper80: number
}

export interface Accuracy {
  mae: number
  rmse: number
  r2: number
}

export interface AnomalyItem {
  date: string
  metric: string
  value: number
  expected: number
  z_score: number
  severity: 'high' | 'medium' | 'low'
  method: string
  title: string
  description: string
}

export interface ForecastResponse {
  metric: string
  days: number
  model: string
  fallback_used: boolean
  history: HistoryPoint[]
  forecast: ForecastPoint[]
  accuracy: Accuracy
  forecast_delta_pct: number
  anomalies: AnomalyItem[]
}

export interface Recommendation {
  title: string
  description: string
  impact: 'high' | 'medium' | 'low'
  category: string
}

export interface RecommendationResponse {
  recommendations: Recommendation[]
  insights: { metric: string; type: string; text: string }[]
}

export interface PipelineStage {
  name: string
  status: string
  duration_ms: number
  rows: number
}

export interface PipelineRun {
  id: number
  job_name: string
  status: 'success' | 'running' | 'failed' | string
  started_at: string
  finished_at: string | null
  rows_processed: number
  stages: PipelineStage[]
}

export interface Freshness {
  latest_data_date: string | null
  age_hours: number | null
  is_fresh: boolean
  metrics_tracked: string[]
  rows_total: number
  last_pipeline_at: string
}

export interface ReportListItem {
  id: number
  title: string
  horizon_days: number
  created_at: string
}

export interface ReportSections {
  executive_summary: string
  key_drivers: { metric: string; trend_pct: number; note: string }[]
  risk_factors: { metric: string; severity: string; note: string }[]
  model_accuracy: { metric: string; model: string; mae: number; rmse: number; r2: number }[]
  next_steps: { step: number; action: string; impact: string; detail: string }[]
  recommendations: { title: string; description: string; impact: string; category: string }[]
}

export interface ReportFull extends ReportListItem {
  sections: ReportSections
}

export interface Settings {
  theme: string
  forecast_days: number
  confidence_level: number
  anomaly_sensitivity: number
}

export interface UploadResponse {
  upload_id: number
  filename: string
  format: string
  rows_valid: number
  rows_rejected: number
  metric_rows_inserted: number
  errors: { row: number; field: string; message: string }[]
}

export interface MetricInfo {
  metric: string
  points: number
  latest_date: string | null
}
