# Task: Full initial build — AI Business Analytics Platform

Implements scope.md phases 1–7 in one task. See blueprints in `.drytis/*.md`.

## Files to create
- `backend/` per architecture.md (app/, api/, ml/, etl/, tests/, requirements.txt)
- `frontend/` per architecture.md (Vite React-TS + Tailwind, 5 pages, components)
- Setup script, 2 background services (already-provisioned Caddy routes on 3000/8000)

## Acceptance criteria
- [ ] `pip install -r backend/requirements.txt` then `pytest backend/tests` all green
- [ ] GET /api/health → {"status":"ok"}
- [ ] GET /api/kpis → 5 KPIs with trend badges (revenue, cac, churn_rate, mrr, projected_growth)
- [ ] POST /api/forecast {metric:"revenue", days:30} → history[] + forecast[] with
      lower/upper bounds + mae/rmse/r2 + anomaly_flags; works for any seeded metric;
      days ∈ {30,60,90} honored
- [ ] GET /api/anomalies → ≥3 seeded anomalies with severity tags (high/medium/low)
- [ ] GET /api/recommendations → ≥4 items across high/medium/low impact
- [ ] POST /api/upload with valid CSV → 200, rows inserted into metric_daily;
      invalid schema (missing columns / non-numeric) → 422 with per-error detail
- [ ] GET /api/pipeline/runs → run history; POST /api/pipeline/run creates run
      with status transition, stages recorded
- [ ] POST /api/reports/generate → stored report containing sections:
      executive_summary, key_drivers, risk_factors, model_accuracy (MAE/RMSE/R²),
      next_steps (≥3 steps); GET /api/reports/{id}/markdown returns markdown
- [ ] GET/PUT /api/settings round-trips theme/forecast_days/confidence_level
- [ ] Frontend: 5 pages navigate via sidebar; dark/light toggle persists; KPI cards
      render real API data; forecast chart shows CI band; anomaly feed + severity
      tags; recommendations panel; upload form works; pipeline table; report
      generate + view + download; no console errors
- [ ] Seed data: 24 months daily, deterministic; anomaly injection present
- [ ] No hardcoded preview URLs / DB creds anywhere in source

## Tests
- Unit: forecast (monotone trend → sensible MAE; bounds widen with horizon),
  anomaly (injected spike flagged; flat series → none), validator (good/bad CSV/JSON)
- Integration (TestClient + SQLite): kpis, forecast, anomalies, recommendations,
  upload valid/invalid, pipeline run, reports generate, settings

## Edge cases
- Empty metric → 404 with detail; days ∉ {30,60,90} → 422
- Upload with duplicate dates → last-write-wins, counted in rows_valid
- < 45 history points → fallback naive forecast still returns valid shape
