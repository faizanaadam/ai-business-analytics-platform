import { AlertTriangle, Flame, Zap } from 'lucide-react'
import type { AnomalyItem } from '../api/types'
import { fmtDate } from '../lib/format'
import { Badge, Card, CardHeader, EmptyState } from './ui'

const sev = {
  high: { icon: Flame, color: 'red' as const, label: 'HIGH' },
  medium: { icon: AlertTriangle, color: 'amber' as const, label: 'MEDIUM' },
  low: { icon: Zap, color: 'blue' as const, label: 'LOW' },
}

export function AnomalyFeed({ anomalies, loading, compact }: {
  anomalies: AnomalyItem[]
  loading: boolean
  compact?: boolean
}) {
  return (
    <Card>
      <CardHeader
        title="Anomaly Detection Feed"
        subtitle="Isolation Forest + Z-score · last 90 days"
        action={<Badge color="slate">{anomalies.length} alerts</Badge>}
      />
      {loading ? (
        <div className="h-40 animate-pulse" />
      ) : anomalies.length === 0 ? (
        <EmptyState message="No anomalies detected in the window." />
      ) : (
        <ul className="max-h-[420px] divide-y divide-slate-100 overflow-auto dark:divide-slate-800">
          {anomalies.map((a, i) => {
            const s = sev[a.severity as keyof typeof sev] ?? sev.low
            const Icon = s.icon
            return (
              <li key={`${a.metric}-${a.date}-${i}`} className="flex gap-3 px-5 py-3.5">
                <span className="mt-0.5 shrink-0">
                  <Icon size={16} className={
                    a.severity === 'high' ? 'text-red-500' : a.severity === 'medium' ? 'text-amber-500' : 'text-blue-500'
                  } />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold">{a.title}</span>
                    <Badge color={s.color}>{s.label}</Badge>
                    <span className="text-xs text-slate-400">{fmtDate(a.date)}</span>
                  </div>
                  {!compact && (
                    <p className="mt-1 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{a.description}</p>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
