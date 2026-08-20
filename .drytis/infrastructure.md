# infrastructure.md

## Proxy routes (Caddy)
| path | port | service |
|---|---|---|
| / | 3000 | frontend-static (`npx serve -s frontend/dist -l 3000`) |
| /api | 8000 | backend-api (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend`) |

## Background services (procmgr)
1. `backend-api` — working dir `/workspace/backend`
2. `frontend-static` — working dir `/workspace/frontend`

## Env vars (backend → `/workspace/backend/.env`)
| key | tag |
|---|---|
| DATABASE_URL | static (mysql+pymysql://user:pass@host:port/db) |
| APP_ENV | app_env |
| APP_NAME | project_name |
| CORS_ORIGINS | static `*` |
| API_HOST/PORT | static |

Frontend has NO env vars needed at runtime (same-origin `/api`).
Build-time only: none (VITE_API_BASE optional override).

## Setup script (runs on every deploy)
```bash
pip install -r backend/requirements.txt
python -m app.seed            # idempotent seed
cd frontend && npm ci && npm run build
```

## Ports
- 3000: frontend static (Caddy `/`)
- 8000: FastAPI (Caddy `/api`)
