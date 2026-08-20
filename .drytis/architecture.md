# architecture.md

## Directory structure
```
/workspace
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app factory, CORS, router mounting
│   │   ├── config.py          # env-driven settings (pydantic-settings)
│   │   ├── db.py              # engine, session factory, get_db dep
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── seed.py            # idempotent 24-month seed (deterministic RNG)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── kpis.py        # GET /kpis
│   │   │   ├── metrics.py     # /metrics routes
│   │   │   ├── forecast.py    # POST /forecast
│   │   │   ├── anomalies.py   # GET /anomalies
│   │   │   ├── recommendations.py
│   │   │   ├── upload.py      # POST /upload (CSV/JSON validation)
│   │   │   ├── pipeline.py    # /pipeline routes (runs, run, freshness)
│   │   │   ├── reports.py     # /reports routes
│   │   │   └── settings_api.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── forecast.py    # hybrid Ridge+RF forecaster w/ bootstrap CI
│   │   │   ├── anomaly.py     # IsolationForest + Z-score
│   │   │   ├── accuracy.py    # MAE/RMSE/R² backtest
│   │   │   └── insights.py    # rule-driven NL insight generation
│   │   └── etl/
│   │       ├── __init__.py
│   │       ├── validator.py   # schema validation for CSV/JSON
│   │       └── ingest.py      # rows → metric_daily
│   ├── tests/
│   │   ├── conftest.py
│     │   ├── test_ml_forecast.py
│   │   ├── test_ml_anomaly.py
│   │   ├── test_etl_validator.py
│   │   ├── test_api_forecast.py
│   │   ├── test_api_reports.py
│   │   └── test_api_upload_pipeline.py
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── api/               # typed client (client.ts, types.ts)
│   │   ├── components/        # KpiCard, ForecastChart, AnomalyFeed,
│   │   │                      # RecommendationPanel, Layout, Sidebar, ThemeToggle,
│   │   │                      # SeverityTag, TrendBadge, Section, Loader
│   │   ├── pages/             # Dashboard, Predictions, PipelineRuns, Reports, Settings
│   │   ├── App.tsx            # router + theme provider
│   │   ├── main.tsx
│   │   └── index.css          # tailwind + custom vars
│   ├── package.json
│   ├── vite.config.ts         # dev proxy → :8000, build outDir dist
│   └── tailwind.config.js     # darkMode: 'class'
│   └── tsconfig.json
├── .drytis/                   # blueprints, specs, cred.json, notes
├── requirements-dev.txt       # (root) pytest etc if needed
└── README.md
```

## Data flow
1. Seed (or upload) → `metric_daily`
2. API layer reads series → `ml.forecast` / `ml.anomaly` / `ml.insights`
3. Reports compose analysis modules → Markdown → `reports` table
4. Frontend consumes JSON only; renders charts/tables; print CSS for PDF

## Routing (Caddy)
- `/` → static frontend, `npx serve -s frontend/dist` on port 3000
- `/api` → uvicorn `app.main:app` port 8000

## Seeding strategy
Deterministic numpy RNG; 24 months of daily data ending "today"; realistic SaaS
patterns: MRR compounding with churn equilibrium, weekly seasonality on revenue,
CAC with ad-spend seasonality, growth trend + noise + injected anomalies
(churn spike ~5 months ago, conversion drop ~3 weeks ago) so anomaly feed has
content on first run.
