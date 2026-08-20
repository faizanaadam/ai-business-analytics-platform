# scope.md

## Modules (in scope)
1. **Dashboard** — KPI cards (Revenue, CAC, Churn Rate, MRR, Projected Growth) with
   trend badges; forecast chart (history + prediction + CI bands, multi-metric);
   anomaly alert feed (severity tags); AI recommendations (High/Med/Low impact).
2. **Predictions** — per-metric 30/60/90-day forecast, model accuracy (MAE/RMSE/R²),
   confidence bounds, anomaly flags on history.
3. **ETL / Pipeline Runs** — CSV/JSON upload with schema validation; ingest into
   metric_daily; simulated pipeline job history (Success/Running/Failed), data
   freshness indicator.
4. **Reports** — "Generate Executive Report" → Markdown with Executive Summary,
   Key Drivers, Risk Factors, Model Accuracy, Strategic Next Steps; list + view +
   download + print-to-PDF.
5. **Settings** — theme toggle, forecast horizon, confidence level, threshold knobs.

## Out of scope
Auth/multi-tenant, real-time streaming, external data source connectors, email delivery.

## Phases (order of work)
1. Blueprints + spec + env keys + scaffold (Vite React-TS, FastAPI skeleton)
2. DB schema + 24-month seed data generator (idempotent)
3. ML engine: forecast.py, anomaly.py, metrics accuracy — unit tests first
4. ETL: schema validation, upload ingestion, pipeline run simulation
5. Insights + reporting module (rule-driven NL generation, markdown builder)
6. API routes wiring everything + integration tests
7. Frontend: layout/nav/theme, API client, all 5 pages
8. Infrastructure gate + review + browser tests

## Acceptance (top-level)
- [ ] First run: platform fully interactive with pre-loaded 24-month dataset
- [ ] GET /api/kpis returns 5 KPI cards with trend badges
- [ ] POST /api/forecast?days=30 returns history+forecast+bounds+metrics for any metric
- [ ] GET /api/anomalies returns severity-tagged anomalies
- [ ] GET /api/recommendations returns High/Med/Low impact actions
- [ ] POST /api/upload accepts valid CSV/JSON, rejects malformed with 422 detail
- [ ] GET /api/pipeline/runs lists job history; POST /api/pipeline/run simulates
- [ ] POST /api/reports/generate produces report with all 5 required sections
- [ ] Dark + light themes; responsive nav on 5 pages; no console errors
