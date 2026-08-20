"""AI recommendations endpoint (rule-driven from live stats)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..ml.forecast import forecast_series
from ..ml.insights import build_insights, build_recommendations
from ..ml.anomaly import detect_anomalies
from .deps import load_series

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

ANALYZED = [
    "revenue", "mrr", "churn_rate", "cac", "conversion_rate", "arpu",
    "new_customers", "active_customers",
]


class RecommendationOut(BaseModel):
    title: str
    description: str
    impact: str
    category: str


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationOut]
    insights: list[dict]


@router.get("", response_model=RecommendationResponse)
def get_recommendations(db: Session = Depends(get_db)):
    all_stats = []
    insights: list[dict] = []
    for metric in ANALYZED:
        series = load_series(db, metric)
        if len(series) < 8:
            continue
        values = [v for _, v in series]
        dates = [d.isoformat() for d, _ in series]
        from .deps import series_stats
        stats = series_stats(series, window=30)
        anomalies = detect_anomalies(metric, values, dates)
        recent_anoms = [a for a in anomalies if dates.index(a.date) >= max(0, len(dates) - 45)]
        fc = forecast_series(values, dates, 30)
        last30 = values[-30:]
        avg_hist = sum(last30) / len(last30)
        avg_fc = sum(fc.values) / len(fc.values)
        stats.update({
            "metric": metric,
            "anomalies_recent": len(recent_anoms),
            "forecast_delta_pct": (avg_fc - avg_hist) / avg_hist * 100 if avg_hist else 0.0,
        })
        all_stats.append(stats)
        insights.extend(build_insights(stats))

    recs = build_recommendations(all_stats)
    order = {"high": 0, "medium": 1, "low": 2}
    recs = sorted(recs, key=lambda r: order.get(r.impact, 3))
    return RecommendationResponse(
        recommendations=[RecommendationOut(**r.__dict__) for r in recs],
        insights=insights,
    )
