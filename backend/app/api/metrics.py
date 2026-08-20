"""Metric history endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import MetricDaily
from .deps import load_series, latest_date

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricInfo(BaseModel):
    metric: str
    points: int
    latest_date: str | None


class HistoryPoint(BaseModel):
    date: str
    value: float


@router.get("", response_model=list[MetricInfo])
def list_metrics(db: Session = Depends(get_db)):
    from sqlalchemy import func, select
    rows = db.execute(
        select(MetricDaily.metric, func.count(MetricDaily.id), func.max(MetricDaily.date))
        .group_by(MetricDaily.metric)
    ).all()
    return [
        MetricInfo(metric=m, points=int(c), latest_date=d.isoformat() if d else None)
        for m, c, d in rows
    ]


@router.get("/{metric}/history", response_model=list[HistoryPoint])
def metric_history(metric: str, days: int = Query(180, ge=7, le=730), db: Session = Depends(get_db)):
    series = load_series(db, metric, days=days)
    if not series:
        raise HTTPException(404, f"no data for metric {metric!r}")
    return [HistoryPoint(date=d.isoformat(), value=round(v, 4)) for d, v in series]
