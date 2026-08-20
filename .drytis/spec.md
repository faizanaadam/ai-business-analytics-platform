# spec.md — AI Business Analytics Platform

## Overview
A full-stack AI analytics platform for SMB/SaaS businesses: ingests daily business
metrics, runs ML forecasting + anomaly detection on top, and surfaces everything on
an interactive dashboard with automated executive reporting.

## Tech stack
| Layer | Choice | Notes |
|---|---|---|
| Frontend | React 18 + TypeScript (Vite 5) | SPA served by Caddy (static `serve`) on port 3000 |
| UI | Tailwind CSS, Lucide icons, Recharts | Dark/light theme, responsive |
| Backend | FastAPI (Python 3.13) | Uvicorn on port 8000, `/api` prefix |
| ORM | SQLAlchemy 2.x + PyMySQL | MySQL auto-provisioned |
| ML | scikit-learn 1.7, pandas, numpy | Ridge + Random Forest hybrid; Isolation Forest + Z-score |
| Reports | Markdown rendered in-app + print CSS | Download `.md`, print-to-PDF from browser |

## Key decisions
- **One dataset, many views**: single `metric_daily` table keyed by (metric, date).
  Metrics: revenue, churn_rate, mrr, cac, new_customers, conversion_rate,
  active_customers, arpu. Keeps ML pipeline metric-agnostic.
- **Forecasting**: hybrid — Ridge regression on engineered features (trend, lags,
  rolling means, day-of-week/month seasonality) when ≥ 45 history points, blended
  with a drift-adjusted seasonal-naive baseline; bootstrap residuals → 80/95%
  confidence bounds. Backtest on last 20% for MAE/RMSE/R².
- **Anomalies**: dual method — Isolation Forest (unsupervised, window features) and
  Z-score vs 28-day rolling baseline; union of flags, severity from |z| bands.
- **Insights**: rule-driven natural-language generation from computed stats (trend
  direction, growth %, anomaly clusters, forecast deltas) — no external LLM needed.
- **Reports**: deterministic Markdown built from the same analysis modules;
  `/reports/{id}.md` raw download; frontend renders + print stylesheet for PDF.
- **Auth**: none (internal analytics tool) — out of scope.

## Non-goals
- Multi-tenancy, user auth, real streaming ingestion (mock ETL instead).
