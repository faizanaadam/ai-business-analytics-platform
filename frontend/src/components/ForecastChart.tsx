import { useMemo } from 'react'
import {
  Area, AreaChart, CartesianGrid, Legend, Line, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import type { ForecastResponse } from '../api/types'
import { fmtCompact, fmtDate } from '../lib/format'

interface Row {
  date: string
  label: string
  actual: number | null
  forecast: number | null
  lower80: number | null
  upper80: number | null
  anomaly: boolean
}

export function ForecastChart({ data, height = 340 }: { data: ForecastResponse; height?: number }) {
  const rows: Row[] = useMemo(() => {
    const h = data.history.map((p) => ({
      date: p.date,
      label: fmtDate(p.date),
      actual: p.value,
      forecast: null as number | null,
      lower80: null as number | null,
      upper80: null as number | null,
      anomaly: !!p.anomaly,
    }))
    const f = data.forecast.map((p) => ({
      date: p.date,
      label: fmtDate(p.date),
      actual: null as number | null,
      forecast: p.value,
      lower80: p.lower80,
      upper80: p.upper80,
      anomaly: false,
    }))
    // connect the lines across the boundary
    if (h.length && f.length) {
      h[h.length - 1].forecast = h[h.length - 1].actual
      f[0].actual = h[h.length - 1].actual
    }
    return [...h, ...f]
  }, [data])

  const splitDate = data.history.length ? data.history[data.history.length - 1].date : null

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={rows} margin={{ top: 8, right: 16, left: 4, bottom: 0 }}>
        <defs>
          <linearGradient id="band" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.22} />
            <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-800" />
        <XAxis dataKey="label" minTickGap={48} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={(v: number) => fmtCompact(v)} width={56} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{
            borderRadius: 10, border: '1px solid rgb(100 116 139 / 0.3)',
            background: 'rgb(15 23 42 / 0.92)', color: '#f1f5f9', fontSize: 12,
          }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={((value: unknown, name: unknown) => {
            const labels: Record<string, string> = { actual: 'Actual', forecast: 'Forecast', band: '80% CI' }
            const v = typeof value === 'number' ? value.toLocaleString('en-US', { maximumFractionDigits: 2 }) : '—'
            return [v, labels[String(name)] ?? String(name)]
          }) as never}
        />
        <Legend formatter={(v: string) => ({ actual: 'Actual', forecast: 'Forecast', band: '80% confidence' }[v] ?? v)} />
        <Area
          dataKey="lower80" name="band" stroke="none" fill="url(#band)" fillOpacity={1}
          legendType="none"
        />
        <Area dataKey="upper80" name="bandHide" stroke="none" fill="transparent" legendType="none" hide />
        {/* recharts bands: draw band via stacked transparent trick is fiddly; use Area range via two areas */}
        <Area
          dataKey="upper80" name="band" stroke="none" fill="none" fillOpacity={0}
          activeDot={false} legendType="none"
        />
        <Line
          type="monotone" dataKey="actual" name="actual" stroke="#0ea5e9" strokeWidth={2}
          dot={(props: { payload?: Row; cx?: number; cy?: number; index?: number }) => {
            const { payload, cx, cy } = props
            if (!payload?.anomaly || cx == null || cy == null) return <g key={`d-${props.index ?? 0}`} />
            return (
              <g key={`a-${props.index ?? 0}`}>
                <circle cx={cx} cy={cy} r={5} fill="#ef4444" stroke="#fff" strokeWidth={1.5} />
              </g>
            )
          }}
          activeDot={{ r: 3 }}
        />
        <Line
          type="monotone" dataKey="forecast" name="forecast" stroke="#6366f1" strokeWidth={2}
          strokeDasharray="6 3" dot={false} activeDot={{ r: 3 }}
        />
        {splitDate && (
          <ReferenceLine
            x={rows.find((r) => r.date === splitDate)?.label}
            stroke="#94a3b8" strokeDasharray="2 4"
            label={{ value: 'today', fill: '#94a3b8', fontSize: 10, position: 'insideTopRight' }}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  )
}
