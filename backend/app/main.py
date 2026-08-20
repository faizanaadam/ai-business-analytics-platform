"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import Base, _get_engine
from .seed import seed
from .api import anomalies, forecast, kpis, metrics, pipeline, recommendations, reports, settings_api, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables + seed on boot (idempotent). MySQL may still be starting
    # after a container pause/resume — retry instead of dying so procmgr
    # doesn't leave the API permanently down (the 502 scenario).
    import asyncio
    import logging

    log = logging.getLogger("app.startup")
    last_err: Exception | None = None
    for attempt in range(1, 11):
        try:
            engine = _get_engine()
            Base.metadata.create_all(engine)
            from .db import get_session_factory
            factory = get_session_factory()
            db = factory()
            try:
                seed(db)
            finally:
                db.close()
            if attempt > 1:
                log.info("startup succeeded on attempt %d", attempt)
            break
        except Exception as e:  # noqa: BLE001 — retry any DB unavailability
            last_err = e
            log.warning("DB not ready (attempt %d/10): %s", attempt, e)
            await asyncio.sleep(9)
    else:
        # Give up: re-raise so the process exits and procmgr respawns it —
        # supervisor-level retry loop with fresh state.
        raise RuntimeError(f"database unreachable after 10 attempts: {last_err}")
    yield


app = FastAPI(title="AI Business Analytics Platform API", version="1.0.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
