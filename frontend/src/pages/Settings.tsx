import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { PageShell } from '../components/Layout'
import { Card, CardHeader } from '../components/ui'
import { useTheme } from '../lib/theme'
import clsx from 'clsx'

export default function Settings() {
  const { theme, toggle } = useTheme()
  const [forecastDays, setForecastDays] = useState(30)
  const [confidence, setConfidence] = useState(0.8)
  const [sensitivity, setSensitivity] = useState(0.75)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.settings()
      .then((s) => {
        setForecastDays(s.forecast_days)
        setConfidence(s.confidence_level)
        setSensitivity(s.anomaly_sensitivity)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function save() {
    setSaved(false)
    setError(null)
    try {
      await api.updateSettings({
        forecast_days: forecastDays,
        confidence_level: confidence,
        anomaly_sensitivity: sensitivity,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <PageShell title="Settings" subtitle="Platform defaults · theme · model parameters">
      <div className="grid max-w-3xl grid-cols-1 gap-6">
        <Card>
          <CardHeader title="Appearance" subtitle="Theme preference (stored per browser)" />
          <div className="flex items-center justify-between p-5">
            <div className="text-sm">
              <div className="font-medium">Dark mode</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Currently: <b className="capitalize">{theme}</b> — click to switch
              </div>
            </div>
            <button
              onClick={toggle}
              role="switch"
              aria-checked={theme === 'dark'}
              className={clsx(
                'relative h-7 w-12 rounded-full transition-colors',
                theme === 'dark' ? 'bg-brand-600' : 'bg-slate-300',
              )}
            >
              <span className={clsx(
                'absolute top-1 h-5 w-5 rounded-full bg-white shadow transition-all',
                theme === 'dark' ? 'left-6' : 'left-1',
              )} />
            </button>
          </div>
        </Card>

        <Card>
          <CardHeader title="Forecasting Defaults" subtitle="Applied to new dashboard sessions" />
          <div className="space-y-6 p-5">
            <div>
              <div className="mb-2 flex justify-between text-sm">
                <span className="font-medium">Default horizon</span>
                <span className="text-slate-500">{forecastDays} days</span>
              </div>
              <div className="flex gap-2">
                {[30, 60, 90].map((d) => (
                  <button
                    key={d}
                    onClick={() => setForecastDays(d)}
                    className={clsx(
                      'flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                      forecastDays === d
                        ? 'border-brand-500 bg-brand-500/10 text-brand-600 dark:text-brand-400'
                        : 'border-slate-300 text-slate-500 hover:border-slate-400 dark:border-slate-700',
                    )}
                  >
                    {d} days
                  </button>
                ))}
              </div>
            </div>

            <Slider
              label="Confidence level"
              value={confidence}
              min={0.5} max={0.99} step={0.01}
              display={`${Math.round(confidence * 100)}%`}
              onChange={setConfidence}
            />
            <Slider
              label="Anomaly sensitivity"
              value={sensitivity}
              min={0.5} max={1.0} step={0.05}
              display={sensitivity.toFixed(2)}
              onChange={setSensitivity}
            />

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={save}
                disabled={loading}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-60"
              >
                Save settings
              </button>
              {saved && <span className="text-sm text-emerald-500">✓ Saved</span>}
              {error && <span className="text-sm text-red-500">{error}</span>}
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="About" />
          <div className="p-5 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
            <p>
              <b className="text-slate-700 dark:text-slate-200">AI Business Analytics Platform</b> — FastAPI +
              scikit-learn backend, React + Recharts frontend. Forecasts use a Ridge + Random
              Forest hybrid with drift-adjusted seasonal-naive blending; anomalies detected via
              Isolation Forest + rolling Z-score.
            </p>
          </div>
        </Card>
      </div>
    </PageShell>
  )
}

function Slider({ label, value, min, max, step, display, onChange }: {
  label: string
  value: number
  min: number
  max: number
  step: number
  display: string
  onChange: (v: number) => void
}) {
  return (
    <div>
      <div className="mb-2 flex justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-slate-500">{display}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-brand-600"
      />
    </div>
  )
}
