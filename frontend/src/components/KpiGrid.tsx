import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import clsx from 'clsx'
import type { KpiCard as KpiCardT } from '../api/types'
import { fmtKpi } from '../lib/format'
import { Card, TrendBadge } from './ui'

const ICONS: Record<string, React.ReactNode> = {
  revenue: '💰',
  cac: '🎯',
  churn_rate: '📉',
  mrr: '📊',
  projected_growth: '🚀',
}

export function KpiGrid({ kpis, loading }: { kpis: KpiCardT[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i} className="h-[118px] animate-pulse">{null}</Card>
        ))}
      </div>
    )
  }
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {kpis.map((k) => {
        const good = (k.trend_pct > 0 && k.good_direction === 'up') || (k.trend_pct < 0 && k.good_direction === 'down')
        return (
          <Card key={k.key} className="p-4">
            <div className="flex items-start justify-between">
              <div className="text-2xl">{ICONS[k.key] ?? '📈'}</div>
              <TrendBadge pct={k.trend_pct} goodDirection={k.good_direction} />
            </div>
            <div className="mt-3 text-2xl font-bold tracking-tight">{fmtKpi(k.value, k.unit)}</div>
            <div className="mt-1 flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
              {k.direction === 'up' ? (
                <ArrowUpRight size={13} className={clsx(good ? 'text-emerald-500' : 'text-red-500')} />
              ) : k.direction === 'down' ? (
                <ArrowDownRight size={13} className={clsx(good ? 'text-emerald-500' : 'text-red-500')} />
              ) : (
                <Minus size={13} />
              )}
              {k.label}
            </div>
          </Card>
        )
      })}
    </div>
  )
}
