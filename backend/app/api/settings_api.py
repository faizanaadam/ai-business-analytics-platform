"""Settings endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Setting

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsOut(BaseModel):
    theme: str
    forecast_days: int
    confidence_level: float
    anomaly_sensitivity: float


class SettingsUpdate(BaseModel):
    theme: str | None = Field(default=None, pattern="^(dark|light)$")
    forecast_days: int | None = Field(default=None, ge=30, le=90)
    confidence_level: float | None = Field(default=None, ge=0.5, le=0.99)
    anomaly_sensitivity: float | None = Field(default=None, ge=0.5, le=1.0)


def _ensure_row(db: Session) -> Setting:
    s = db.query(Setting).get(1)
    if not s:
        s = Setting(id=1)
        db.add(s)
        db.commit()
    return s


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    s = _ensure_row(db)
    return SettingsOut(
        theme=s.theme, forecast_days=s.forecast_days,
        confidence_level=float(s.confidence_level),
        anomaly_sensitivity=float(s.anomaly_sensitivity),
    )


@router.put("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    s = _ensure_row(db)
    if payload.theme is not None:
        s.theme = payload.theme
    if payload.forecast_days is not None:
        s.forecast_days = payload.forecast_days
    if payload.confidence_level is not None:
        s.confidence_level = payload.confidence_level
    if payload.anomaly_sensitivity is not None:
        s.anomaly_sensitivity = payload.anomaly_sensitivity
    db.commit()
    return SettingsOut(
        theme=s.theme, forecast_days=s.forecast_days,
        confidence_level=float(s.confidence_level),
        anomaly_sensitivity=float(s.anomaly_sensitivity),
    )
