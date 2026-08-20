import { ArrowRight, Lightbulb } from 'lucide-react'
import type { Recommendation } from '../api/types'
import { Badge, Card, CardHeader, EmptyState } from './ui'

const IMPACT = {
  high: { color: 'red' as const, label: 'High Impact', ring: 'ring-1 ring-red-500/30' },
  medium: { color: 'amber' as const, label: 'Medium Impact', ring: 'ring-1 ring-amber-500/30' },
  low: { color: 'blue' as const, label: 'Low Impact', ring: 'ring-1 ring-blue-500/30' },
}

export function RecommendationPanel({ recommendations, loading }: {
  recommendations: Recommendation[]
  loading: boolean
}) {
  return (
    <Card>
      <CardHeader
        title="AI Recommendations"
        subtitle="Ranked by urgency · updated live"
        action={<Lightbulb size={16} className="text-amber-400" />}
      />
      {loading ? (
        <div className="h-40 animate-pulse" />
      ) : recommendations.length === 0 ? (
        <EmptyState message="No recommendations available." />
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {recommendations.map((r, i) => {
            const imp = IMPACT[r.impact as keyof typeof IMPACT] ?? IMPACT.low
            return (
              <li key={i} className={`px-5 py-4 ${imp.ring} rounded-lg m-2 bg-slate-50/50 dark:bg-slate-800/30`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500/10 text-[11px] font-bold text-brand-600 dark:text-brand-400">
                      {i + 1}
                    </span>
                    <h4 className="text-sm font-semibold">{r.title}</h4>
                  </div>
                  <Badge color={imp.color}>{imp.label}</Badge>
                </div>
                <p className="mt-2 pl-8 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{r.description}</p>
                <div className="mt-2 flex items-center gap-1 pl-8 text-[10px] uppercase tracking-wider text-slate-400">
                  <ArrowRight size={10} /> {r.category.replace('_', ' ')}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
