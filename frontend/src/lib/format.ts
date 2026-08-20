// Formatting helpers

export function fmtNumber(v: number, digits = 0): string {
  return v.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits })
}

export function fmtCompact(v: number): string {
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`
  if (Math.abs(v) >= 10_000) return `${(v / 1000).toFixed(1)}k`
  return v.toLocaleString('en-US', { maximumFractionDigits: 1 })
}

export function fmtCurrency(v: number): string {
  return `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

export function fmtPercent(v: number, digits = 1): string {
  return `${v.toFixed(digits)}%`
}

export function fmtKpi(v: number, unit: string): string {
  if (unit === 'currency') return fmtCurrency(v)
  if (unit === 'percent') return fmtPercent(v, 2)
  return fmtNumber(v)
}

export function fmtDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
}

export function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export function fmtDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function fmtDelta(v: number): string {
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`
}

export const METRIC_LABELS: Record<string, string> = {
  revenue: 'Revenue',
  mrr: 'MRR',
  churn_rate: 'Churn Rate',
  cac: 'CAC',
  new_customers: 'New Customers',
  conversion_rate: 'Conversion Rate',
  active_customers: 'Active Customers',
  arpu: 'ARPU',
}
