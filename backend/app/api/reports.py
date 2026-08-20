"""Automated executive report generation."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..ml.forecast import forecast_series
from ..ml.insights import build_insights, build_recommendations
from ..models import Report
from .deps import load_series, series_stats
from .recommendations import ANALYZED

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut(BaseModel):
    id: int
    title: str
    horizon_days: int
    created_at: datetime
    sections: dict


class ReportListItem(BaseModel):
    id: int
    title: str
    horizon_days: int
    created_at: datetime


def _fmt(v: float, kind: str) -> str:
    if kind == "currency":
        return f"${v:,.0f}"
    if kind == "percent":
        return f"{v:.2f}%"
    return f"{v:,.0f}"


def build_report(db: Session, horizon: int) -> Report:
    # --- gather stats + forecasts for key metrics ---
    from ..ml.anomaly import detect_anomalies
    stats_all = []
    forecasts = {}
    for metric in ANALYZED:
        series = load_series(db, metric)
        if len(series) < 8:
            continue
        values = [v for _, v in series]
        dates = [d.isoformat() for d, _ in series]
        st = series_stats(series, 30)
        st["metric"] = metric
        fc = forecast_series(values, dates, horizon)
        forecasts[metric] = fc
        last30 = values[-30:]
        avg_hist = sum(last30) / len(last30)
        avg_fc = sum(fc.values) / len(fc.values)
        st["forecast_delta_pct"] = (avg_fc - avg_hist) / avg_hist * 100 if avg_hist else 0
        anoms = detect_anomalies(metric, values, dates)
        st["anomalies_recent"] = sum(
            1 for a in anoms if dates.index(a.date) >= len(dates) - 45
        )
        stats_all.append(st)

    recs = build_recommendations(stats_all)

    by = {s["metric"]: s for s in stats_all}
    rev, mrr, churn, cac = by.get("revenue"), by.get("mrr"), by.get("churn_rate"), by.get("cac")

    # --- executive summary ---
    parts = []
    if rev:
        parts.append(
            f"Revenue over the last 30 days averaged {_fmt(rev['recent_avg'], 'currency')}/day "
            f"({rev['trend_pct']:+.1f}% vs prior 30 days)."
        )
    if mrr:
        parts.append(f"MRR stands at {_fmt(mrr['latest'], 'currency')}, trending {mrr['trend_pct']:+.1f}%.")
    if churn:
        parts.append(f"Monthly churn is at {churn['latest']:.2f}% ({churn['trend_pct']:+.1f}% trend).")
    if cac:
        parts.append(f"CAC is {_fmt(cac['recent_avg'], 'currency')}, moving {cac['trend_pct']:+.1f}%.")
    fc_delta = forecasts.get("revenue")
    if fc_delta:
        f_rev = fc_delta
        end_lo, end_hi = f_rev.lower80[-1], f_rev.upper80[-1]
        parts.append(
            f"The forecasting model projects revenue to end the {horizon}-day horizon between "
            f"${end_lo:,.0f} and ${end_hi:,.0f}/day (80% confidence)."
        )
    executive_summary = " ".join(parts)

    # --- key drivers ---
    drivers = []
    for s in sorted(stats_all, key=lambda x: abs(x.get("trend_pct", 0)), reverse=True)[:4]:
        drivers.append({
            "metric": s["metric"],
            "trend_pct": round(s["trend_pct"], 1),
            "note": (
                f"{s['metric'].replace('_',' ').title()} moved {s['trend_pct']:+.1f}% over the last 30 days "
                f"vs the prior window (avg {_fmt(s['recent_avg'], 'percent' if 'rate' in s['metric'] or s['metric']=='arpu' else 'currency')})."
            ),
        })
    # attach forecast deltas as drivers too
    for m, fc in forecasts.items():
        s = by.get(m)
        if s and abs(s.get("forecast_delta_pct", 0)) >= 4:
            drivers.append({
                "metric": m,
                "trend_pct": round(s["forecast_delta_pct"], 1),
                "note": f"Forecast projects {m.replace('_',' ')} {s['forecast_delta_pct']:+.1f}% over the next {horizon} days.",
            })

    # --- risks ---
    from ..ml.anomaly import detect_anomalies
    risks = []
    for metric in ["churn_rate", "cac", "conversion_rate"]:
        series = load_series(db, metric)
        if len(series) < 14:
            continue
        values = [v for _, v in series]
        dates = [d.isoformat() for d, _ in series]
        anoms = detect_anomalies(metric, values, dates)
        recent = [a for a in anoms if dates.index(a.date) >= len(dates) - 45]
        if recent:
            worst = max(recent, key=lambda a: abs(a.z_score))
            risks.append({
                "metric": metric,
                "severity": worst.severity,
                "note": (
                    f"{len(recent)} anomaly(ies) in the last 45 days on {metric.replace('_',' ')}; "
                    f"most recent {worst.date} hit {worst.value:,.2f} vs expected {worst.expected:,.2f}."
                ),
            })
    for s in stats_all:
        if s["metric"] in ("churn_rate", "cac") and s.get("forecast_delta_pct", 0) > 5:
            risks.append({
                "metric": s["metric"],
                "severity": "medium",
                "note": f"Forecast projects {s['metric'].replace('_',' ')} worsening {s['forecast_delta_pct']:+.1f}% over {horizon} days.",
            })
    if not risks:
        risks.append({"metric": "none", "severity": "low", "note": "No material risks flagged by the model."})

    # --- accuracy ---
    accuracy_rows = []
    for m, fc in forecasts.items():
        accuracy_rows.append({
            "metric": m,
            "model": fc.model_name,
            "mae": fc.accuracy["mae"],
            "rmse": fc.accuracy["rmse"],
            "r2": fc.accuracy["r2"],
        })

    # --- next steps ---
    next_steps = [
        {
            "step": i + 1,
            "action": r.title,
            "impact": r.impact,
            "detail": r.description,
        }
        for i, r in enumerate(recs[:6])
    ]
    while len(next_steps) < 3:
        next_steps.append({
            "step": len(next_steps) + 1,
            "action": "Review forecast accuracy weekly",
            "impact": "low",
            "detail": "Compare model predictions vs actuals weekly and re-tune if MAE drifts >20%.",
        })

    sections = {
        "executive_summary": executive_summary,
        "key_drivers": drivers,
        "risk_factors": risks,
        "model_accuracy": accuracy_rows,
        "next_steps": next_steps,
        "recommendations": [
            {"title": r.title, "description": r.description, "impact": r.impact, "category": r.category}
            for r in recs
        ],
    }

    # --- markdown ---
    md = [f"# Executive Analytics Report", ""]
    md.append(f"*Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} — {horizon}-day horizon*")
    md += ["", "## Executive Summary", "", executive_summary, ""]
    md += ["## Key Drivers", ""]
    for d in drivers:
        md.append(f"- {d['note']}")
    md += ["", "## Risk Factors", ""]
    for r in risks:
        md.append(f"- **[{r['severity'].upper()}]** {r['note']}")
    md += ["", "## Model Accuracy (backtest, last 20% holdout)", "",
           "| Metric | Model | MAE | RMSE | R² |", "|---|---|---|---|---|"]
    for a in accuracy_rows:
        md.append(f"| {a['metric']} | {a['model']} | {a['mae']:.2f} | {a['rmse']:.2f} | {a['r2']:.3f} |")
    md += ["", "## Strategic Next Steps", ""]
    for s in next_steps:
        md.append(f"{s['step']}. **{s['action']}** ({s['impact']} impact) — {s['detail']}")
    md += ["", "## AI Recommendations", ""]
    for r in sections["recommendations"]:
        md.append(f"- **[{r['impact'].upper()} IMPACT]** {r['title']}: {r['description']}")
    content_md = "\n".join(md)

    report = Report(
        title=f"Executive Analytics Report — {datetime.utcnow().strftime('%Y-%m-%d')}",
        horizon_days=horizon, content_md=content_md, sections=sections,
        created_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[ReportListItem])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(Report.created_at.desc()).limit(50).all()


@router.post("/generate", response_model=ReportOut)
def generate_report(horizon_days: int = 30, db: Session = Depends(get_db)):
    from ..ml.forecast import ALLOWED_HORIZONS
    if horizon_days not in ALLOWED_HORIZONS:
        raise HTTPException(422, f"horizon_days must be one of {list(ALLOWED_HORIZONS)}")
    report = build_report(db, horizon_days)
    return ReportOut(
        id=report.id, title=report.title, horizon_days=report.horizon_days,
        created_at=report.created_at, sections=report.sections,
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(Report).get(report_id)
    if not r:
        raise HTTPException(404, f"report {report_id} not found")
    return ReportOut(id=r.id, title=r.title, horizon_days=r.horizon_days,
                     created_at=r.created_at, sections=r.sections)


@router.get("/{report_id}/markdown", response_class=PlainTextResponse)
def get_report_markdown(report_id: int, db: Session = Depends(get_db)):
    r = db.query(Report).get(report_id)
    if not r:
        raise HTTPException(404, f"report {report_id} not found")
    return r.content_md
