"""ETL pipeline simulation endpoints."""
from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PipelineRun, MetricDaily
from .deps import latest_date

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

PIPELINE_JOBS = ["extract_transactions", "transform_metrics", "load_warehouse", "train_models"]


class StageOut(BaseModel):
    name: str
    status: str
    duration_ms: int
    rows: int = 0


class PipelineRunOut(BaseModel):
    id: int
    job_name: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    rows_processed: int
    stages: list[StageOut]

    class Config:
        from_attributes = True


@router.get("/runs", response_model=list[PipelineRunOut])
def list_runs(limit: int = 25, db: Session = Depends(get_db)):
    runs = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit).all()
    return runs


@router.post("/run", response_model=PipelineRunOut)
def run_pipeline(db: Session = Depends(get_db)):
    """Simulate a full ETL+train cycle synchronously (fast, deterministic-ish)."""
    import random
    random.seed()  # per-run variance
    run = PipelineRun(job_name="full_etl", status="running", started_at=datetime.utcnow(), rows_processed=0, stages=[])
    db.add(run)
    db.commit()
    db.refresh(run)

    total_rows = db.query(MetricDaily).count()
    stages: list[dict] = []
    statuses = []
    for job in PIPELINE_JOBS:
        t0 = time.perf_counter()
        duration_ms = int((time.perf_counter() - t0 + random.uniform(0.02, 0.09)) * 1000)
        status = "success"
        if job == "train_models" and random.random() < 0.08:
            status = "failed"
        statuses.append(status)
        rows = random.randint(40000, 52000) if job != "train_models" else 0
        stages.append({"name": job, "status": status, "duration_ms": duration_ms, "rows": rows})
        if status == "failed":
            break

    final = "failed" if "failed" in statuses else "success"
    run.status = final
    run.finished_at = datetime.utcnow()
    run.rows_processed = total_rows if final == "success" else 0
    run.stages = stages
    db.commit()
    db.refresh(run)
    return run


@router.get("/freshness")
def freshness(db: Session = Depends(get_db)):
    latest = latest_date(db)
    metrics = db.query(MetricDaily.metric).distinct().all()
    now = datetime.utcnow()
    age_hours = None
    fresh = False
    if latest:
        age_hours = round((now - datetime.combine(latest, datetime.min.time())).total_seconds() / 3600, 1)
        fresh = age_hours <= 48
    last_run = db.query(PipelineRun.started_at).order_by(PipelineRun.started_at.desc()).first()
    return {
        "latest_data_date": latest.isoformat() if latest else None,
        "age_hours": age_hours,
        "is_fresh": fresh,
        "metrics_tracked": [m[0] for m in metrics],
        "rows_total": db.query(MetricDaily).count(),
        "last_pipeline_at": last_run[0].isoformat() if last_run else None,
    }
