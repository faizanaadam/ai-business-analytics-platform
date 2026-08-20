"""Shared query helpers for API routes."""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import MetricDaily


def load_series(db: Session, metric: str, days: int | None = None) -> list[tuple[date, float]]:
    """Ordered (date, value) ascending for a metric."""
    q = select(MetricDaily.date, MetricDaily.value).where(MetricDaily.metric == metric).order_by(MetricDaily.date)
    if days:
        latest = db.execute(select(func.max(MetricDaily.date)).where(MetricDaily.metric == metric)).scalar()
        if latest is None:
            return []
        q = q.where(MetricDaily.date >= date.fromordinal(latest.toordinal() - days + 1))
    return [(d, float(v)) for d, v in db.execute(q).all()]


def latest_date(db: Session, metric: str | None = None) -> date | None:
    q = select(func.max(MetricDaily.date))
    if metric:
        q = q.where(MetricDaily.metric == metric)
    return db.execute(q).scalar()


def series_stats(series: list[tuple[date, float]], window: int = 30) -> dict:
    """Recent vs prior window averages + trend pct."""
    vals = [v for _, v in series]
    if not vals:
        return {"recent_avg": 0.0, "prior_avg": 0.0, "trend_pct": 0.0, "latest": 0.0}
    recent = vals[-window:]
    prior = vals[-2 * window:-window] if len(vals) >= 2 * window else vals[: window]
    recent_avg = sum(recent) / len(recent)
    prior_avg = sum(prior) / len(prior) if prior else recent_avg
    return {
        "recent_avg": recent_avg,
        "prior_avg": prior_avg,
        "trend_pct": (recent_avg - prior_avg) / prior_avg * 100 if prior_avg else 0.0,
        "latest": vals[-1],
    }
