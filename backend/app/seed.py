"""Deterministic 24-month seed: realistic SaaS business metrics with injected
anomalies so the anomaly feed has content on first run."""
from __future__ import annotations

import sys
from datetime import date, timedelta

import numpy as np

from .db import Base, get_session_factory, _get_engine
from .models import MetricDaily, PipelineRun, Setting

METRICS = [
    "revenue", "mrr", "churn_rate", "cac", "new_customers",
    "conversion_rate", "active_customers", "arpu",
]

DAYS = 24 * 30  # ~24 months


def generate_series(days: int, end: date) -> dict[str, list[tuple[date, float]]]:
    rng = np.random.default_rng(42)
    dates = [end - timedelta(days=days - 1 - i) for i in range(days)]
    n = days
    t = np.arange(n, dtype=float)

    # --- customers: compounding growth with churn equilibrium ---
    active = np.zeros(n)
    active[0] = 4200.0
    base_churn = 0.0125  # ~1.25%/day? no — monthly 1.6% → daily ~0.053%
    # churn_rate metric = monthly churn % of active base (2.5–4.5%)
    churn_monthly = 3.2 + 0.15 * np.sin(2 * np.pi * t / 120) + rng.normal(0, 0.25, n)
    # injected anomaly: churn spike ~150 days ago lasting ~12 days
    spike_start = n - 150
    churn_monthly[spike_start:spike_start + 12] += rng.uniform(1.8, 2.6, 12)
    churn_daily = churn_monthly / 100.0 / 30.0

    new_cust = np.maximum(18, 42 + 0.012 * t + 8 * np.sin(2 * np.pi * t / 7.0) + rng.normal(0, 6, n))
    # injected anomaly: acquisition dip ~70 days ago
    dip_start = n - 70
    new_cust[dip_start:dip_start + 10] *= 0.62

    for i in range(1, n):
        lost = active[i - 1] * churn_daily[i]
        active[i] = max(500.0, active[i - 1] + new_cust[i] - lost)

    # --- MRR: active × ARPU, ARPU slowly rising ---
    arpu = 48.0 + 0.018 * t + rng.normal(0, 1.1, n)
    arpu = np.clip(arpu, 30, None)
    mrr = active * arpu

    # --- revenue: daily recognized ~ MRR/30 with weekly seasonality + noise ---
    dow = np.array([d.weekday() for d in dates], dtype=float)
    weekly = 1.0 + 0.16 * np.sin(2 * np.pi * (dow + 1) / 7.0)
    revenue = mrr / 30.0 * weekly * (1 + rng.normal(0, 0.035, n))
    # injected anomaly: one-day revenue surge ~45 days ago (big deal)
    surge_idx = n - 45
    revenue[surge_idx] *= 2.2
    revenue[surge_idx + 1] *= 1.15

    # --- CAC: seasonal ad spend, rising slowly ---
    cac = 95.0 + 0.02 * t + 9 * np.sin(2 * np.pi * t / 90.0) + rng.normal(0, 4.5, n)
    cac = np.clip(cac, 45, None)
    # injected anomaly: CAC spike ~100 days ago (campaign misfire)
    cac[n - 100:n - 100 + 8] += rng.uniform(28, 40, 8)

    # --- conversion rate: improving trend with a 3-week-old drop ---
    conv = 3.1 + 0.0022 * t + 0.25 * np.sin(2 * np.pi * t / 60.0) + rng.normal(0, 0.18, n)
    conv = np.clip(conv, 0.8, None)
    conv[n - 21:n - 21 + 12] -= rng.uniform(0.8, 1.2, 12)  # anomaly: conversion drop

    return {
        "revenue": list(zip(dates, revenue)),
        "mrr": list(zip(dates, mrr)),
        "churn_rate": list(zip(dates, churn_monthly)),
        "cac": list(zip(dates, cac)),
        "new_customers": list(zip(dates, new_cust)),
        "conversion_rate": list(zip(dates, conv)),
        "active_customers": list(zip(dates, active)),
        "arpu": list(zip(dates, arpu)),
    }


def seed(db) -> None:
    """Idempotent: skips if metric_daily already populated."""
    existing = db.query(MetricDaily.id).limit(1).count()
    if existing:
        return

    end = date.today()
    series = generate_series(DAYS, end)

    rows: list[MetricDaily] = []
    for metric, pts in series.items():
        for d, v in pts:
            rows.append(MetricDaily(metric=metric, date=d, value=round(float(v), 4)))

    db.add_all(rows)
    db.commit()

    # default settings row
    if not db.query(Setting.id).filter(Setting.id == 1).count():
        db.add(Setting(id=1, theme="dark", forecast_days=30, confidence_level=0.80, anomaly_sensitivity=0.75))
        db.commit()

    # a few historical pipeline runs so the run history is non-empty
    from datetime import datetime, timedelta as _td
    now = datetime.utcnow()
    jobs = [
        ("extract_transactions", "success", 12, 48210),
        ("transform_metrics", "success", 9, 48210),
        ("load_warehouse", "success", 7, 48210),
        ("train_models", "success", 23, 0),
        ("extract_transactions", "success", 11, 47820),
        ("transform_metrics", "failed", 4, 47820),
    ]
    start = now - _td(hours=13)
    for j, (name, status, secs, rws) in enumerate(jobs):
        started = start + _td(minutes=j * 17)
        db.add(PipelineRun(
            job_name=name, status=status, started_at=started,
            finished_at=started + _td(seconds=secs),
            rows_processed=rws,
            stages=[
                {"name": "extract", "status": "success", "duration_ms": secs * 220, "rows": rws},
                {"name": "transform", "status": status, "duration_ms": secs * 310, "rows": rws},
                {"name": "load", "status": "success" if status == "success" else "skipped",
                 "duration_ms": secs * 410, "rows": rws if status == "success" else 0},
            ],
        ))
    db.commit()


def main() -> None:
    engine = _get_engine()
    Base.metadata.create_all(engine)
    factory = get_session_factory()
    db = factory()
    try:
        seed(db)
        count = db.query(MetricDaily).count()
        print(f"seed complete — {count} metric rows")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
