"""Anomaly feed endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..ml.anomaly import detect_anomalies
from .deps import load_series

router = APIRouter(prefix="/anomalies", tags=["anomalies"])

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class AnomalyOut(BaseModel):
    date: str
    metric: str
    value: float
    expected: float
    z_score: float
    severity: str
    method: str
    title: str
    description: str


def _describe(metric: str, a) -> tuple[str, str]:
    from_name = metric.replace("_", " ")
    delta = a.value - a.expected
    pct = (delta / a.expected * 100) if a.expected else 0.0
    direction = "spike" if delta > 0 else "drop"
    titles = {
        "churn_rate": f"Churn {direction}",
        "revenue": f"Revenue {direction}",
        "cac": f"CAC {direction}",
        "conversion_rate": f"Conversion {direction}",
    }
    title = titles.get(metric, f"{from_name.title()} {direction}")
    desc = (
        f"{from_name.title()} {direction}d to {a.value:,.2f} on {a.date} "
        f"(expected ≈ {a.expected:,.2f}, {pct:+.1f}% vs baseline). "
        f"Detected via {a.method.replace('_', ' ')} ({a.severity} severity)."
    )
    return title, desc


@router.get("", response_model=list[AnomalyOut])
def list_anomalies(
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(90, ge=7, le=365),
    sensitivity: float = Query(0.75, ge=0.5, le=1.0),
    db: Session = Depends(get_db),
):
    from ..etl.validator import KNOWN_METRICS
    out: list[AnomalyOut] = []
    for metric in KNOWN_METRICS:
        series = load_series(db, metric)
        if len(series) < 14:
            continue
        values = [v for _, v in series]
        dates = [d.isoformat() for d, _ in series]
        # only anomalies in the requested window
        cutoff_idx = max(0, len(series) - days)
        for a in detect_anomalies(metric, values, dates, sensitivity=sensitivity):
            if dates.index(a.date) >= cutoff_idx:
                title, desc = _describe(metric, a)
                out.append(AnomalyOut(
                    date=a.date, metric=metric, value=a.value, expected=a.expected,
                    z_score=a.z_score, severity=a.severity, method=a.method,
                    title=title, description=desc,
                ))
    out.sort(key=lambda a: (SEVERITY_ORDER.get(a.severity, 3), a.date), reverse=False)
    out.sort(key=lambda a: SEVERITY_ORDER.get(a.severity, 3))
    return out[:limit]
