"""Forecast endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..ml.forecast import ALLOWED_HORIZONS, forecast_series
from ..ml.anomaly import detect_anomalies
from .deps import load_series

router = APIRouter(prefix="/forecast", tags=["forecast"])


class ForecastRequest(BaseModel):
    metric: str = Field(min_length=1, max_length=40)
    days: int = Field(default=30)
    include_history_days: int = Field(default=90, ge=14, le=365)
    anomaly_sensitivity: float = Field(default=0.75, ge=0.5, le=1.0)


class HistoryPoint(BaseModel):
    date: str
    value: float
    anomaly: bool


class ForecastPoint(BaseModel):
    date: str
    value: float
    lower95: float
    upper95: float
    lower80: float
    upper80: float


@router.post("")
def forecast(req: ForecastRequest, db: Session = Depends(get_db)):
    if req.days not in ALLOWED_HORIZONS:
        raise HTTPException(422, f"days must be one of {list(ALLOWED_HORIZONS)}")

    full = load_series(db, req.metric)
    if len(full) < 8:
        raise HTTPException(404, f"not enough data for metric {req.metric!r} ({len(full)} points)")

    values = [v for _, v in full]
    dates = [d.isoformat() for d, _ in full]

    anomalies = detect_anomalies(req.metric, values, dates, sensitivity=req.anomaly_sensitivity)
    anomaly_dates = {a.date for a in anomalies}

    fc = forecast_series(values, dates, req.days)

    hist_window = full[-req.include_history_days:]
    history = [
        HistoryPoint(date=d.isoformat(), value=round(float(v), 4), anomaly=(d.isoformat() in anomaly_dates))
        for d, v in hist_window
    ]

    forecast_pts = [
        ForecastPoint(date=d, value=v, lower95=lo95, upper95=hi95, lower80=lo80, upper80=hi80)
        for d, v, lo80, hi80, lo95, hi95 in zip(
            fc.dates, fc.values, fc.lower80, fc.upper80, fc.lower95, fc.upper95
        )
    ]

    hist_vals = [v for _, v in hist_window]
    last30 = hist_vals[-30:] if len(hist_vals) >= 30 else hist_vals
    avg_hist = sum(last30) / len(last30)
    avg_fc = sum(fc.values) / len(fc.values)
    delta = (avg_fc - avg_hist) / avg_hist * 100 if avg_hist else 0.0

    return {
        "metric": req.metric,
        "days": req.days,
        "model": fc.model_name,
        "fallback_used": fc.fallback_used,
        "history": [h.model_dump() for h in history],
        "forecast": [p.model_dump() for p in forecast_pts],
        "accuracy": fc.accuracy,
        "forecast_delta_pct": round(delta, 2),
        "anomalies": [
            {
                "date": a.date, "value": a.value, "expected": a.expected,
                "z_score": a.z_score, "severity": a.severity, "method": a.method,
            }
            for a in anomalies
        ],
    }
