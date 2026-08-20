import { useState } from 'react'
import { CheckCircle2, Clock, Play, RefreshCw, Upload, XCircle } from 'lucide-react'
import { api } from '../api/client'
import { useApi } from '../lib/hooks'
import { PageShell } from '../components/Layout'
import { Badge, Card, CardHeader, ErrorBox } from '../components/ui'
import type { PipelineRun } from '../api/types'
import { fmtDateTime, fmtDuration, fmtNumber } from '../lib/format'
import type { UploadResponse } from '../api/types'

export default function PipelineRuns() {
  const runs = useApi<PipelineRun[]>(() => api.pipelineRuns(), [])
  const freshness = useApi(() => api.freshness(), [])
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    setUploadError(null)
    try {
      const res = await api.upload(file)
      setUploadResult(res)
      freshness.reload()
    } catch (err) {
      setUploadError((err as Error).message)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function handleRun() {
    setRunning(true)
    setRunError(null)
    try {
      await api.runPipeline()
      runs.reload()
      freshness.reload()
    } catch (err) {
      setRunError((err as Error).message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <PageShell
      title="Pipeline Runs"
      subtitle="ETL simulation · ingestion · data freshness"
      actions={
        <button
          onClick={handleRun}
          disabled={running}
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-60"
        >
          <Play size={13} /> {running ? 'Running…' : 'Run pipeline now'}
        </button>
      }
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Job Run History"
            subtitle="Extract → transform → load → train"
            action={
              <button onClick={runs.reload} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
                <RefreshCw size={14} />
              </button>
            }
          />
          {runs.error && <div className="p-4"><ErrorBox message={runs.error} /></div>}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-400 dark:border-slate-800">
                  <th className="px-5 py-3">Job</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3">Started</th>
                  <th className="px-3 py-3">Duration</th>
                  <th className="px-3 py-3 text-right">Rows</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {runs.loading ? (
                  <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">Loading…</td></tr>
                ) : (runs.data ?? []).map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="px-5 py-3 font-medium">{r.job_name.replace(/_/g, ' ')}</td>
                    <td className="px-3 py-3"><StatusBadge status={r.status} /></td>
                    <td className="px-3 py-3 text-slate-500">{fmtDateTime(r.started_at)}</td>
                    <td className="px-3 py-3 text-slate-500">
                      {r.finished_at ? fmtDuration((new Date(r.finished_at).getTime() - new Date(r.started_at).getTime())) : '—'}
                    </td>
                    <td className="px-3 py-3 text-right text-slate-500">{fmtNumber(r.rows_processed)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Data Freshness" />
            <div className="space-y-2.5 p-5 text-sm">
              {freshness.loading ? (
                <div className="text-slate-400">Checking…</div>
              ) : freshness.data ? (
                <>
                  <Row label="Latest data" value={freshness.data.latest_data_date ?? '—'} />
                  <Row label="Age" value={freshness.data.age_hours != null ? `${freshness.data.age_hours}h` : '—'} />
                  <Row label="Status" value={freshness.data.is_fresh ? '✅ Fresh' : '⚠️ Stale'} />
                  <Row label="Rows tracked" value={fmtNumber(freshness.data.rows_total)} />
                  <Row label="Last pipeline" value={fmtDateTime(freshness.data.last_pipeline_at)} />
                  <div className="pt-2 text-[11px] text-slate-400">
                    Metrics: {freshness.data.metrics_tracked.join(', ')}
                  </div>
                </>
              ) : null}
            </div>
          </Card>

          <Card>
            <CardHeader title="Upload Data" subtitle="CSV or JSON · auto schema validation" />
            <div className="p-5">
              <label className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed border-slate-300 px-4 py-8 text-center transition-colors hover:border-brand-500 hover:bg-brand-50/50 dark:border-slate-700 dark:hover:border-brand-500 dark:hover:bg-brand-950/20">
                <Upload size={22} className="text-brand-500" />
                <span className="text-sm font-medium">
                  {uploading ? 'Validating & ingesting…' : 'Click to upload CSV / JSON'}
                </span>
                <span className="text-xs text-slate-400">
                  Columns: date, metric, value — or wide format (date, revenue, mrr, …)
                </span>
                <input type="file" accept=".csv,.json" className="hidden" onChange={handleUpload} disabled={uploading} />
              </label>

              {uploadError && <div className="mt-4"><ErrorBox message={uploadError} /></div>}
              {runError && <div className="mt-4"><ErrorBox message={runError} /></div>}

              {uploadResult && (
                <div className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm">
                  <div className="font-semibold text-emerald-600 dark:text-emerald-400">
                    ✅ {uploadResult.filename} ingested
                  </div>
                  <div className="mt-1.5 text-xs text-slate-600 dark:text-slate-300">
                    {uploadResult.rows_valid} valid rows · {uploadResult.rows_rejected} rejected · {uploadResult.metric_rows_inserted} points stored
                  </div>
                  {uploadResult.errors.length > 0 && (
                    <ul className="mt-2 space-y-1 text-xs text-amber-600 dark:text-amber-400">
                      {uploadResult.errors.slice(0, 5).map((e, i) => (
                        <li key={i}>Row {e.row} [{e.field}]: {e.message}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </PageShell>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'success') {
    return <Badge color="green"><CheckCircle2 size={11} /> Success</Badge>
  }
  if (status === 'failed') {
    return <Badge color="red"><XCircle size={11} /> Failed</Badge>
  }
  return <Badge color="amber"><Clock size={11} /> Running</Badge>
}
