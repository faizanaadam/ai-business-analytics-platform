# Product Requirements Document (PRD)

## AI Business Analytics Platform

| | |
|---|---|
| **Version** | 1.0 |
| **Status** | Shipped — v1.0 complete, verified (43/43 tests, infra audit PASS, browser tests 8/8) |
| **Date** | 2026-08-20 |
| **Owner** | Product / Engineering |

---

## 1. Overview

A full-stack analytics platform that processes business metrics, trains predictive
models on them, and surfaces automated AI insights on an interactive dashboard.
Target user: SMB/SaaS operators who want executive-grade analytics without a
data team.

**Problem:** Business data exists but insights don't. Operators can't forecast
revenue, don't notice anomalies until quarter-end, and spend hours assembling
status reports manually.

**Solution:** One platform that ingests metric data, runs ML forecasting and
anomaly detection automatically, explains what's happening in plain language,
and generates a board-ready executive report in one click.

## 2. Goals & Success Metrics

| Goal | Metric |
|---|---|
| Forecast future performance | Revenue/MRR forecast within R² ≥ 0.4 on noisy daily data (backtested) |
| Catch anomalies early | Injected spikes/drops flagged with correct severity, no false high/medium alerts on flat data |
| Zero-effort reporting | Executive report generated in < 10s with all 5 required sections |
| Instant time-to-value | Fully interactive on first run with pre-loaded 24-month dataset |

## 3. Personas

- **CEO/Founder** — reads the dashboard weekly, generates the executive report for board meetings.
- **Growth/Marketing lead** — watches CAC, conversion anomalies, forecast trends.
- **Ops/Data engineer** — uploads CSV/JSON extracts, monitors pipeline runs and data freshness.

## 4. Scope

**In scope (v1.0):** dashboard with 5 KPI cards, forecasting engine, anomaly
feed, AI recommendations, ETL simulation with upload ingestion, automated
executive reporting, dark/light UI with 5 pages, seeded demo data.

**Out of scope (v1):** authentication/multi-tenancy, real-time streaming
ingestion, external data-source connectors, email delivery of reports.

## 5. Functional Requirements

### 5.1 Interactive Insight Dashboard
- 5 KPI cards: Revenue, CAC, Churn Rate, MRR, Projected Growth — each with
  ▲/▼ trend badge (% vs prior 30 days) and favorable-direction logic (CAC down = good).
- Trend & forecasting chart: history + predicted values + 80% confidence band;
  forecast drawn dashed; anomaly points marked; "today" divider line.
- Anomaly alert feed: severity tags (HIGH/MEDIUM/LOW), plain-language
  descriptions, sorted by severity then recency.
- AI recommendations panel: numbered actions with High/Medium/Low impact
  badges and category tags (growth/retention/efficiency/data quality).

### 5.2 Prediction & Forecasting Engine
- Hybrid model: Ridge regression (trend, lags, rolling means, weekly
  seasonality features) + Random Forest, blended with drift-adjusted
  seasonal-naive; falls back to naive under 45 history points.
- Horizons: 30/60/90 days. All 8 tracked metrics supported.
- Backtest on last 20% holdout → MAE, RMSE, R² per metric.
- Bootstrap residual confidence bounds (80% and 95%), widening with horizon.
- Structured JSON: history (with anomaly flags), forecast (with bounds),
  accuracy metrics, forecast delta %.

### 5.3 Data Ingestion & ETL Simulation
- Upload CSV or JSON; long format (`date,metric,value`) or wide format
  (`date,revenue,mrr,...`); date and currency-symbol tolerance.
- Schema validation with per-row error reporting (`{row, field, message}`),
  422 on structural mismatch; 25 MB streamed cap; CSV parse errors → 422.
- Upsert semantics (last-write-wins on duplicate date+metric).
- Pipeline run history (Success/Running/Failed) with per-stage detail,
  simulated full-ETL trigger, data-freshness timestamps.

### 5.4 Automated AI Reporting
- "Generate Executive Report" button → stored report containing: Executive
  Summary, Key Drivers, Risk Factors, Model Accuracy (MAE/RMSE/R² table),
  Strategic Next Steps (numbered, impact-tagged).
- Rule-driven NL insight generation from live stats — deterministic,
  no external LLM dependency.
- Markdown download + print-to-PDF stylesheet.

### 5.5 UI/UX
- Dark/light theme (persisted per browser), responsive sidebar nav
  (Dashboard, Predictions, Pipeline Runs, Reports, Settings).
- Pre-loaded deterministic 24-month mock dataset with 5 injected anomalies
  (churn spike, acquisition dip, revenue surge, CAC spike, conversion drop).

## 6. Technical Architecture

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript (Vite), Tailwind CSS, Lucide, Recharts |
| Backend | FastAPI (Python 3.13), SQLAlchemy 2.x, MySQL |
| ML | scikit-learn (Ridge, RandomForest, IsolationForest), numpy |
| Serving | Caddy — `/` → static SPA (port 3000), `/api` → FastAPI (port 8000) |

Structure: `backend/app/{api,ml,etl}` — ML modules are pure functions (no DB
access); API layer owns persistence; frontend is a typed SPA consuming JSON only.

## 7. Data Model

- **metric_daily** (metric, date, value) — unique per metric+date; 8 metrics.
- **pipeline_runs** (job_name, status, started/finished_at, rows, stages JSON)
- **uploads** (filename, format, rows_valid/rejected, validation_errors JSON)
- **reports** (title, horizon, content_md, sections JSON)
- **settings** (theme, forecast_days, confidence_level, anomaly_sensitivity)

## 8. API Specification

| Method | Route | Purpose |
|---|---|---|
| GET | /api/health | liveness |
| GET | /api/kpis | 5 KPI cards + trends |
| GET | /api/metrics | metric inventory + freshness |
| GET | /api/metrics/{m}/history | history points |
| POST | /api/forecast | forecast + bounds + accuracy + anomalies |
| GET | /api/anomalies | severity-tagged feed |
| GET | /api/recommendations | ranked actions + NL insights |
| POST | /api/upload | validate + ingest CSV/JSON |
| GET | /api/pipeline/runs | job history |
| POST | /api/pipeline/run | simulate ETL run |
| GET | /api/pipeline/freshness | data freshness |
| GET/POST | /api/reports[/generate] | list / build executive report |
| GET | /api/reports/{id}[/markdown] | fetch / download report |
| GET/PUT | /api/settings | platform settings |

## 9. ML Approach

- **Forecasting:** feature-engineered Ridge + RF ensemble, walk-forward
  prediction, naive-baseline blend weighted by backtest error; bootstrap
  residual quantiles scaled by √horizon for asymmetric bands.
- **Anomaly detection:** union of Isolation Forest (value/rolling-mean/rolling-std
  features, z-corroboration gate) and rolling 28-day Z-score; severity bands
  |z| ≥ 3.5 high, ≥ 3.0 medium, else low; chained-noise suppression.
- **Insights/recommendations:** 15+ deterministic rules over cross-metric
  stats (trend %, forecast delta, anomaly clusters) → prioritized actions.

## 10. Non-Functional Requirements

- **Security:** parameterized SQL only (SQLAlchemy), no path traversal on
  upload (in-memory validation), upload size/row caps, no secrets in source.
- **Reliability:** idempotent seed, upsert-safe ingestion, health endpoint,
  procmgr-supervised services with auto-respawn.
- **Testability:** 43 automated tests (unit + API integration) — ML pure
  functions tested in isolation; API tests run on SQLite (hermetic).
- **Deployability:** single setup script (install → seed → build); env vars
  managed via backend env-keys; config tar reproducible.

## 11. Future Roadmap

1. Auth + multi-tenancy
2. Real connectors (Stripe, Google Analytics, Meta Ads)
3. Scheduled report email delivery
4. ARIMA/Prophet model comparison + automatic model selection
5. Anomaly root-cause drill-down
