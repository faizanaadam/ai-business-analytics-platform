# patterns.md

## Backend
- FastAPI routers under `app/api/`, each `router = APIRouter()` with own prefix.
- Pydantic v2 models for request/response in the route module that owns them.
- DB via `Depends(get_db)`; sessions closed by context manager.
- Never raw SQL strings — SQLAlchemy ORM / Core expressions only.
- ML modules are **pure functions**: take numpy arrays / list[dict], return
  dataclasses/dicts. No DB access inside `ml/` — keeps them unit-testable.
- Errors: HTTPException with machine-readable `detail`; upload validation returns
  422 with per-row error list.
- All env access through `app.config.Settings` (pydantic-settings) — no os.getenv
  scattered around.

## Testing
- pytest; unit tests for ml/etl (pure functions, synthetic arrays); API tests via
  fastapi TestClient with SQLite in-memory override (no MySQL dependency in CI).
- Test names: `test_<unit>_<scenario>`.

## Frontend
- Function components + hooks only; typed API client returns typed interfaces.
- No `any` (eslint-checked). Tailwind utility classes; semantic color tokens via
  CSS vars (`--color-primary` etc.) so dark/light theme swap works.
- Charts: Recharts; every chart wrapped in `ResponsiveContainer`.
- API base: `import.meta.env.VITE_API_BASE ?? ''` → same-origin `/api` in prod.
- Components < 200 lines; pages compose components; shared formatting utils in
  `src/lib/format.ts`.

## Git
- Conventional commits: `feat:`, `fix:`, `chore:`, `test:`, `docs:`.
