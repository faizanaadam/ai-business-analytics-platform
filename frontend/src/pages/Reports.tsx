import { useState } from 'react'
import { Download, FileText, Loader2, Printer, Sparkles } from 'lucide-react'
import { api } from '../api/client'
import { useApi } from '../lib/hooks'
import { PageShell } from '../components/Layout'
import { Badge, Card, CardHeader, EmptyState } from '../components/ui'
import type { ReportFull } from '../api/types'
import { fmtDateTime } from '../lib/format'

const HORIZONS = [30, 60, 90] as const

export default function Reports() {
  const list = useApi(() => api.reports(), [])
  const [selected, setSelected] = useState<ReportFull | null>(null)
  const [generating, setGenerating] = useState(false)
  const [horizon, setHorizon] = useState<number>(30)
  const [genError, setGenError] = useState<string | null>(null)

  async function generate() {
    setGenerating(true)
    setGenError(null)
    try {
      const r = await api.generateReport(horizon)
      setSelected(r)
      list.reload()
    } catch (e) {
      setGenError((e as Error).message)
    } finally {
      setGenerating(false)
    }
  }

  async function openReport(id: number) {
    const r = await api.report(id)
    setSelected(r)
  }

  const s = selected?.sections

  return (
    <PageShell
      title="Executive Reports"
      subtitle="Automated AI-generated summaries with model accuracy and strategic next steps"
      actions={
        <>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-900"
          >
            {HORIZONS.map((h) => <option key={h} value={h}>{h}-day horizon</option>)}
          </select>
          <button
            onClick={generate}
            disabled={generating}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-60"
          >
            {generating ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
            {generating ? 'Generating…' : 'Generate Executive Report'}
          </button>
        </>
      }
    >
      {genError && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
          {genError}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* list */}
        <Card className="lg:col-span-1">
          <CardHeader title="Report History" subtitle={`${list.data?.length ?? 0} reports`} />
          <div className="max-h-[560px] overflow-auto">
            {list.loading ? (
              <div className="p-5 text-sm text-slate-400">Loading…</div>
            ) : (list.data ?? []).length === 0 ? (
              <EmptyState message="No reports yet — generate one above." />
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {(list.data ?? []).map((r) => (
                  <li key={r.id}>
                    <button
                      onClick={() => openReport(r.id)}
                      className={`w-full px-4 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/40 ${
                        selected?.id === r.id ? 'bg-brand-50 dark:bg-brand-950/30' : ''
                      }`}
                    >
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <FileText size={13} className="text-brand-500" />
                        Report #{r.id}
                      </div>
                      <div className="mt-0.5 text-[11px] text-slate-400">
                        {fmtDateTime(r.created_at)} · {r.horizon_days}d horizon
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>

        {/* detail */}
        <div className="lg:col-span-3">
          {!selected ? (
            <Card>
              <EmptyState message="Select a report or generate a new one." />
            </Card>
          ) : (
            <Card className="print-area">
              <div className="no-print flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
                <div>
                  <h2 className="text-base font-bold">{selected.title}</h2>
                  <p className="text-xs text-slate-400">
                    {fmtDateTime(selected.created_at)} · {selected.horizon_days}-day horizon
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => window.print()}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                  >
                    <Printer size={13} /> Print / PDF
                  </button>
                  <a
                    href={api.reportMarkdownUrl(selected.id)}
                    download={`executive-report-${selected.id}.md`}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
                  >
                    <Download size={13} /> Markdown
                  </a>
                </div>
              </div>

              {s && (
                <div className="space-y-7 p-6">
                  <section>
                    <SectionTitle>Executive Summary</SectionTitle>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                      {s.executive_summary}
                    </p>
                  </section>

                  <section>
                    <SectionTitle>Key Drivers</SectionTitle>
                    <ul className="mt-2 space-y-2">
                      {s.key_drivers.map((d, i) => (
                        <li key={i} className="flex items-start gap-2.5 rounded-lg bg-slate-50 px-3.5 py-2.5 text-sm dark:bg-slate-800/50">
                          <span className={`mt-0.5 text-xs font-bold ${d.trend_pct >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                            {d.trend_pct >= 0 ? '▲' : '▼'}
                          </span>
                          {d.note}
                        </li>
                      ))}
                    </ul>
                  </section>

                  <section>
                    <SectionTitle>Risk Factors</SectionTitle>
                    <ul className="mt-2 space-y-2">
                      {s.risk_factors.map((r, i) => (
                        <li key={i} className="flex items-start gap-2.5 rounded-lg bg-slate-50 px-3.5 py-2.5 text-sm dark:bg-slate-800/50">
                          <Badge color={r.severity === 'high' ? 'red' : r.severity === 'medium' ? 'amber' : 'slate'}>
                            {r.severity.toUpperCase()}
                          </Badge>
                          <span className="text-slate-600 dark:text-slate-300">{r.note}</span>
                        </li>
                      ))}
                    </ul>
                  </section>

                  <section>
                    <SectionTitle>Model Accuracy</SectionTitle>
                    <div className="mt-2 overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead>
                          <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wider text-slate-400 dark:border-slate-800">
                            <th className="py-2 pr-4">Metric</th>
                            <th className="py-2 pr-4">Model</th>
                            <th className="py-2 pr-4">MAE</th>
                            <th className="py-2 pr-4">RMSE</th>
                            <th className="py-2">R²</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {s.model_accuracy.map((a) => (
                            <tr key={a.metric}>
                              <td className="py-2 pr-4 font-medium">{a.metric.replace(/_/g, ' ')}</td>
                              <td className="py-2 pr-4 text-slate-500">{a.model}</td>
                              <td className="py-2 pr-4">{a.mae.toFixed(2)}</td>
                              <td className="py-2 pr-4">{a.rmse.toFixed(2)}</td>
                              <td className="py-2">{a.r2.toFixed(3)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>

                  <section>
                    <SectionTitle>Strategic Next Steps</SectionTitle>
                    <ol className="mt-2 space-y-2.5">
                      {s.next_steps.map((n) => (
                        <li key={n.step} className="flex gap-3 rounded-lg border border-slate-200 px-4 py-3 dark:border-slate-800">
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-500/10 text-xs font-bold text-brand-600 dark:text-brand-400">
                            {n.step}
                          </span>
                          <div>
                            <div className="text-sm font-semibold">{n.action}</div>
                            <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{n.detail}</div>
                          </div>
                          <Badge color={n.impact === 'high' ? 'red' : n.impact === 'medium' ? 'amber' : 'blue'}>
                            {n.impact}
                          </Badge>
                        </li>
                      ))}
                    </ol>
                  </section>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </PageShell>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-l-2 border-brand-500 pl-2.5 text-xs font-bold uppercase tracking-widest text-brand-600 dark:text-brand-400">
      {children}
    </h3>
  )
}
