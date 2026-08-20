import { useEffect, useState } from 'react'
import { Activity, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import { useApi } from '../lib/hooks'
import { PageShell } from '../components/Layout'
import { KpiGrid } from '../components/KpiGrid'
import { ForecastChart } from '../components/ForecastChart'
import { AnomalyFeed } from '../components/AnomalyFeed'
import { RecommendationPanel } from '../components/RecommendationPanel'
import { Badge, Card, CardHeader, ErrorBox, Spinner } from '../components/ui'
import type { ForecastResponse, Freshness } from '../api/types'
import { fmtDelta, fmtDate } from '../lib/format'

const FORECAST_METRICS = ['revenue', 'mrr'] as const

export default function Dashboard() {
  const kpis = useApi(() => api.kpis(), [])
  const anomalies = useApi(() => api.anomalies(12), [])
  const recs = useApi(() => api.recommendations(), [])
  const freshness = useApi<Freshness>(() => api.freshness(), [])
  const [chartMetric, setChartMetric] = useState<string>('revenue')
  const forecast = useApi<ForecastResponse>(
    () => api.forecast(chartMetric, 30),
    [chartMetric],
  )
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => { /* re-fetch everything on manual refresh */ }, [reloadKey])

  return (
    <PageShell
      title="Insight Dashboard"
      subtitle={
        freshness.data
          ? `Data through ${freshness.data.latest_data_date ? fmtDate(freshness.data.latest_data_date) : '—'} · ${freshness.data.rows_total.toLocaleString()} rows tracked`
          : 'Loading data status…'
      }
      actions={
        <>
          {freshness.data && (
            <Badge color={freshness.data.is_fresh ? 'green' : 'amber'}>
              <Activity size={11} />
              {freshness.data.is_fresh ? 'Data fresh' : `Data ${freshness.data.age_hours}h old`}
            </Badge>
          )}
          <button
            onClick={() => { setReloadKey((k) => k + 1); kpis.reload(); anomalies.reload(); recs.reload(); freshness.reload(); }}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </>
      }
    >
      {kpis.error && <ErrorBox message={`KPIs: ${kpis.error}`} />}

      <KpiGrid kpis={kpis.data ?? []} loading={kpis.loading} />

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Trend & Forecast"
            subtitle="30-day projection with 80% confidence band · anomaly points marked"
            action={
              <div className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
                {FORECAST_METRICS.map((m) => (
                  <button
                    key={m}
                    onClick={() => setChartMetric(m)}
                    className={`rounded-md px-3 py-1 text-xs font-semibold uppercase ${
                      chartMetric === m
                        ? 'bg-white text-brand-600 shadow dark:bg-slate-900 dark:text-brand-400'
                        : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            }
          />
          <div className="p-4">
            {forecast.loading ? (
              <div className="h-[340px]"><Spinner label="Training forecast model…" /></div>
            ) : forecast.error ? (
              <ErrorBox message={forecast.error} />
            ) : forecast.data ? (
              <>
                <ForecastChart data={forecast.data} />
                <div className="mt-3 flex flex-wrap items-center gap-3 px-2 text-xs text-slate-500 dark:text-slate-400">
                  <span>Model: <b>{forecast.data.model}</b></span>
                  <span>30d change: <b className={forecast.data.forecast_delta_pct >= 0 ? 'text-emerald-500' : 'text-red-500'}>
                    {fmtDelta(forecast.data.forecast_delta_pct)}
                  </b></span>
                  <span>MAE {forecast.data.accuracy.mae.toFixed(1)} · RMSE {forecast.data.accuracy.rmse.toFixed(1)} · R² {forecast.data.accuracy.r2.toFixed(3)}</span>
                </div>
              </>
            ) : null}
          </div>
        </Card>

        <AnomalyFeed anomalies={anomalies.data ?? []} loading={anomalies.loading} />
      </div>

      <div className="mt-6">
        {recs.data && recs.data.insights.length > 0 && (
          <Card className="mb-6">
            <CardHeader title="AI Insights" subtitle="Generated from live metric analysis" />
            <ul className="grid grid-cols-1 gap-3 p-5 md:grid-cols-2">
              {recs.data.insights.slice(0, 6).map((ins, i) => (
                <li key={i} className="flex items-start gap-2.5 rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 dark:bg-slate-800/50 dark:text-slate-300">
                  <span className="mt-0.5 text-brand-500">◆</span>
                  {ins.text}
                </li>
              ))}
            </ul>
          </Card>
        )}
        <RecommendationPanel
          recommendations={recs.data?.recommendations ?? []}
          loading={recs.loading}
        />
      </div>
    </PageShell>
  )
}
