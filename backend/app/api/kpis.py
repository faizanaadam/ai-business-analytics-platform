"""KPI endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..ml.forecast import forecast_series, ALLOWED_HORIZONS
from .deps import load_series, series_stats

router = APIRouter(prefix="/kpis", tags=["kpis"])


class KpiCard(BaseModel):
    key: str
    label: str
    value: float
    unit: str  # currency | percent | count
    trend_pct: float
    direction: str  # up | down | flat
    good_direction: str  # up | down (which way is favorable)


LABELS = {
    "revenue": ("Revenue (30d avg)", "currency", "up"),
    "cac": ("Customer Acquisition Cost", "currency", "down"),
    "churn_rate": ("Churn Rate", "percent", "down"),
    "mrr": ("MRR", "currency", "up"),
}


@router.get("", response_model=list[KpiCard])
def get_kpis(db: Session = Depends(get_db)):
    cards: list[KpiCard] = []
    for key, (label, unit, good) in LABELS.items():
        series = load_series(db, key, days=90)
        stats = series_stats(series, window=30)
        value = stats["recent_avg"]
        trend = stats["trend_pct"]
        direction = "up" if trend > 1 else ("down" if trend < -1 else "flat")
        cards.append(KpiCard(
            key=key, label=label, value=round(value, 2), unit=unit,
            trend_pct=round(trend, 2), direction=direction, good_direction=good,
        ))

    # projected growth: MRR forecast delta over default horizon
    mrr_series = load_series(db, "mrr", days=None)  # full history for the model
    if len(mrr_series) >= 8:
        fc = forecast_series(
            [v for _, v in mrr_series], [d.isoformat() for d, _ in mrr_series], 30
        )
        hist_last30 = [v for _, v in mrr_series[-30:]]
        avg_hist = sum(hist_last30) / len(hist_last30)
        avg_fc = sum(fc.values) / len(fc.values)
        delta = (avg_fc - avg_hist) / avg_hist * 100 if avg_hist else 0.0
        cards.append(KpiCard(
            key="projected_growth", label="Projected Growth (30d)", value=round(delta, 2),
            unit="percent", trend_pct=round(delta, 2),
            direction="up" if delta > 1 else ("down" if delta < -1 else "flat"),
            good_direction="up",
        ))
    return cards
