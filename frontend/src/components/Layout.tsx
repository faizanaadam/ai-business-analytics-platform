import { NavLink } from 'react-router-dom'
import {
  Activity, BarChart3, BrainCircuit, FileText, LayoutDashboard,
  Menu, Moon, Settings as SettingsIcon, Sun, TrendingUp, X,
} from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { useTheme } from '../lib/theme'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/predictions', label: 'Predictions', icon: TrendingUp },
  { to: '/pipeline', label: 'Pipeline Runs', icon: Activity },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

export function Sidebar() {
  const [open, setOpen] = useState(false)
  const { theme, toggle } = useTheme()

  const links = NAV.map(({ to, label, icon: Icon, end }) => (
    <NavLink
      key={to}
      to={to}
      end={end}
      onClick={() => setOpen(false)}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-brand-600 text-white shadow'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200',
        )
      }
    >
      <Icon size={17} />
      {label}
    </NavLink>
  ))

  return (
    <>
      {/* mobile top bar */}
      <div className="no-print sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur md:hidden dark:border-slate-800 dark:bg-slate-950/90">
        <div className="flex items-center gap-2">
          <button onClick={() => setOpen(!open)} aria-label="Menu" className="rounded-lg p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
          <BrandMark />
        </div>
        <ThemeButton theme={theme} toggle={toggle} />
      </div>

      {open && (
        <div className="no-print border-b border-slate-200 bg-white px-4 py-3 md:hidden dark:border-slate-800 dark:bg-slate-950">
          <nav className="flex flex-col gap-1">{links}</nav>
        </div>
      )}

      {/* desktop sidebar */}
      <aside className="no-print fixed inset-y-0 left-0 z-20 hidden w-60 flex-col border-r border-slate-200 bg-white md:flex dark:border-slate-800 dark:bg-slate-950">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <BrandMark />
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3">{links}</nav>
        <div className="border-t border-slate-200 px-5 py-4 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 dark:text-slate-500">v1.0 · FastAPI + React</span>
            <ThemeButton theme={theme} toggle={toggle} />
          </div>
        </div>
      </aside>
    </>
  )
}

function BrandMark() {
  return (
    <>
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow">
        <BrainCircuit size={18} />
      </span>
      <div className="leading-tight">
        <div className="text-sm font-bold tracking-tight">Analytics AI</div>
        <div className="text-[10px] uppercase tracking-widest text-slate-400">Business Intelligence</div>
      </div>
    </>
  )
}

function ThemeButton({ theme, toggle }: { theme: string; toggle: () => void }) {
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
    >
      {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  )
}

export function PageShell({ title, subtitle, actions, children }: {
  title: string
  subtitle?: string
  actions?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="md:pl-60">
      <header className="no-print flex flex-wrap items-center justify-between gap-3 px-4 pt-6 pb-4 md:px-8">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold tracking-tight md:text-2xl">
            <BarChart3 className="text-brand-500" size={22} />
            {title}
          </h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      <main className="print-area px-4 pb-10 md:px-8">{children}</main>
    </div>
  )
}
