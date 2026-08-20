# schema.md

## Tables (MySQL)

### metric_daily
| col | type | notes |
|---|---|---|
| id | INT PK AI | |
| metric | VARCHAR(40) | indexed; e.g. revenue, churn_rate |
| date | DATE | indexed |
| value | DECIMAL(14,2) | |

UNIQUE(metric, date). Business metrics tracked: revenue, mrr, churn_rate, cac,
new_customers, conversion_rate, active_customers, arpu.

### pipeline_runs
| col | type | notes |
|---|---|---|
| id | INT PK AI | |
| job_name | VARCHAR(60) | extract_transactions, transform_metrics, load_warehouse, train_models |
| status | VARCHAR(12) | success / running / failed |
| started_at | DATETIME | |
| finished_at | DATETIME | nullable |
| rows_processed | INT | |
| records | JSON | per-stage detail |

### uploads
| col | type | notes |
|---|---|---|
| id | INT PK AI | |
| filename | VARCHAR(200) | |
| source_format | VARCHAR(6) | csv / json |
| rows_valid | INT | |
| rows_rejected | INT | |
| metric_rows_inserted | INT | |
| validation_errors | JSON | |
| created_at | DATETIME | |

### reports
| col | type | notes |
|---|---|---|
| id | INT PK AI | |
| title | VARCHAR(120) | |
| horizon_days | INT | |
| content_md | TEXT | full markdown |
| sections | JSON | structured {executive_summary, key_drivers, risk_factors, accuracy, next_steps} |
| created_at | DATETIME | |

### settings
Single row (id=1): theme, forecast_days, confidence_level, anomaly_sensitivity.

## API routes
| method | path | purpose |
|---|---|---|
| GET | /api/health | liveness |
| GET | /api/kpis | 5 KPI cards + trend badges |
| GET | /api/metrics | list available metrics + latest date (freshness) |
| GET | /api/metrics/{name}/history?days= | history points |
| POST | /api/forecast | {metric, days} → history + forecast + bounds + accuracy + anomaly flags |
| GET | /api/anomalies?limit= | severity-tagged anomaly feed |
| GET | /api/recommendations | High/Med/Low impact actions |
| POST | /api/upload | multipart CSV/JSON → validate → ingest |
| GET | /api/pipeline/runs | job run history |
| POST | /api/pipeline/run | simulate a pipeline execution |
| GET | /api/pipeline/freshness | data freshness timestamps |
| GET | /api/reports | list reports |
| POST | /api/reports/generate | build + store exec report |
| GET | /api/reports/{id} | single report JSON |
| GET | /api/reports/{id}/markdown | raw markdown download |
| GET | /api/settings | get settings |
| PUT | /api/settings | update settings |
