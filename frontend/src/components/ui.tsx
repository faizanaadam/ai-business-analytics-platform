import clsx from 'clsx'

export function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={clsx(
      'rounded-xl border border-slate-200 bg-white shadow-sm',
      'dark:border-slate-800 dark:bg-slate-900',
      className,
    )}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action }: {
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
      <div>
        <h3 className="text-sm font-semibold tracking-wide text-slate-900 dark:text-slate-100">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Badge({ children, color }: { children: React.ReactNode; color: 'green' | 'red' | 'amber' | 'blue' | 'slate' | 'violet' }) {
  const colors = {
    green: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 ring-emerald-500/20',
    red: 'bg-red-500/10 text-red-600 dark:text-red-400 ring-red-500/20',
    amber: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 ring-amber-500/20',
    blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 ring-blue-500/20',
    slate: 'bg-slate-500/10 text-slate-600 dark:text-slate-400 ring-slate-500/20',
    violet: 'bg-violet-500/10 text-violet-600 dark:text-violet-400 ring-violet-500/20',
  }
  return (
    <span className={clsx('inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset', colors[color])}>
      {children}
    </span>
  )
}

export function TrendBadge({ pct, goodDirection }: { pct: number; goodDirection: 'up' | 'down' }) {
  const up = pct > 0
  const flat = Math.abs(pct) < 0.5
  if (flat) {
    return <Badge color="slate">→ 0.0%</Badge>
  }
  const good = (up && goodDirection === 'up') || (!up && goodDirection === 'down')
  return (
    <Badge color={good ? 'green' : 'red'}>
      {up ? '▲' : '▼'} {pct > 0 ? '+' : ''}{pct.toFixed(1)}%
    </Badge>
  )
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-slate-500 dark:text-slate-400">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-500 dark:border-slate-700" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  )
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
      {message}
    </div>
  )
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-slate-400">
      <span className="text-sm">{message}</span>
    </div>
  )
}
