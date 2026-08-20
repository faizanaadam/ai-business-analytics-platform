import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useApi } from '../lib/hooks'
import { PageShell } from '../components/Layout'
import { ForecastChart } from '../components/ForecastChart'
import { Badge, Card, CardHeader, ErrorBox } from '../components/ui'
import type { ForecastResponse, MetricInfo } from '../api/types'
import { METRIC_LABELS, fmtDelta } from '../lib/format'
import { AnomalyFeed } from '../components/AnomalyFeed'

const HORIZONS = [30, 60, 90] as const
const METRICS = ['revenue', 'mrr', 'churn_rate', 'cac', 'new_customers', 'conversion_rate', 'active_customers', 'arpu']

export default function Predictions() {
  const [metric, setMetric] = useState('revenue')
  const [days, setDays] = useState<number>(30)
  const [historyDays, setHistoryDays] = useState(90)
  const [result, setResult] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const metricsInfo = useApi<MetricInfo[]>(() => api.metrics(), [])

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    api.forecast(metric, days, 0.75, historyDays)
      .then((r) => alive && setResult(r))
      .catch((e: Error) => alive && setError(e.message))
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [metric, days, historyDays])

  return (
    <PageShell
      title="Prediction & Forecasting"
      subtitle="Scikit-learn hybrid model · backtested accuracy · confidence intervals"
      actions={
        <div className="flex gap-1 rounded-lg bg-slate-100 p-1 dark:bg-slate-800">
          {HORIZONS.map((h) => (
            <button
              key={h}
              onClick={() => setDays(h)}
              className={`rounded-md px-3 py-1 text-xs font-semibold ${
                days === h
                  ? 'bg-white text-brand-600 shadow dark:bg-slate-900 dark:text-brand-400'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              {h}d
            </button>
          ))}
        </div>
      }
    >
      <Card className="mb-6">
        <CardHeader title="Model Inputs" subtitle="Choose a metric and history window" />
        <div className="flex flex-wrap items-end gap-4 p-5">
          <label className="flex flex-col gap-1.5 text-xs font-medium text-slate-500">
            Metric
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="w-48 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            >
              {METRICS.map((m) => (
                <option key={m} value={m}>{METRIC_LABELS[m] ?? m}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-medium text-slate-500">
            History window
            <select
              value={historyDays}
              onChange={(e) => setHistoryDays(Number(e.target.value))}
              className="w-40 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            >
              {[90, 180, 365].map((d) => (
                <option key={d} value={d}>Last {d} days</option>
              ))}
            </select>
          </label>
          {metricsInfo.data && (
            <div className="ml-auto flex flex-wrap gap-2">
              {metricsInfo.data.slice(0, 3).map((mi) => (
                <Badge key={mi.metric} color="slate">
                  {METRIC_LABELS[mi.metric] ?? mi.metric}: {mi.points.toLocaleString()} pts
                </Badge>
              ))}
            </div>
          )}
        </div>
      </Card>

      {error && <ErrorBox message={error} />}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title={`${METRIC_LABELS[metric] ?? metric} — ${days}-day forecast`}
            subtitle={loading ? 'Training…' : `Model: ${result?.model} · ${result?.fallback_used ? 'fallback (short history)' : 'hybrid ML'}`}
          />
          <div className="p-4">
            {loading ? (
              <div className="h-[380px] animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
            ) : result ? (
              <ForecastChart data={result} height={380} />
            ) : null}
          </div>
        </Card>

        <div className="space-y-6">
          {result && (
            <Card>
              <CardHeader title="Model Accuracy" subtitle="Backtest on last 20% holdout" />
              <div className="grid grid-cols-3 divide-x divide-slate-100 dark:divide-slate-800">
                {[
                  { k: 'MAE', v: result.accuracy.mae },
                  { k: 'RMSE', v: result.accuracy.rmse },
                  { k: 'R²', v: result.accuracy.r2 },
                ].map(({ k, v }) => (
                  <div key={k} className="px-4 py-4 text-center">
                    <div className="text-lg font-bold">{v.toFixed(2)}</div>
                    <div className="text-[11px] uppercase tracking-wider text-slate-400">{k}</div>
                  </div>
                ))}
              </div>
              <div className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
                Forecast {days}-day change: <b className={result.forecast_delta_pct >= 0 ? 'text-emerald-500' : 'text-red-500'}>
                  {fmtDelta(result.forecast_delta_pct)}
                </b>
              </div>
            </Card>
          )}
          <AnomalyFeed anomalies={result?.anomalies.map(a => ({ ...a, metric, title: a.metric === metric ? `${METRIC_LABELS[metric] ?? metric} variance` : a.title })) ?? []} loading={loading} compact />
        </div>
      </div>
    </PageShell>
  )
}
