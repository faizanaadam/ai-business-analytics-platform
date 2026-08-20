"""Rule-driven natural-language insight + recommendation generation.

Pure functions: consume computed statistics, emit NL strings + structured
recommendations. No DB access, no LLM call — deterministic and testable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Recommendation:
    title: str
    description: str
    impact: str  # high / medium / low
    category: str  # growth / retention / efficiency / data_quality


def _pct_change(recent: float, prior: float) -> float:
    if prior == 0:
        return 0.0
    return (recent - prior) / abs(prior) * 100.0


def build_insights(stats: dict) -> list[dict]:
    """stats keys: metric, recent_avg, prior_avg, trend_pct, anomalies_recent (int),
    forecast_delta_pct, series_min/max etc. Returns NL insight dicts."""
    out: list[dict] = []
    m = stats.get("metric", "metric")
    trend = stats.get("trend_pct", 0.0)
    fc = stats.get("forecast_delta_pct", 0.0)
    anomalies = stats.get("anomalies_recent", 0)

    direction = "rising" if trend > 1 else ("falling" if trend < -1 else "stable")
    out.append({
        "metric": m,
        "type": "trend",
        "text": (
            f"{m.replace('_', ' ').title()} is {direction} — last 30 days averaged "
            f"{stats.get('recent_avg', 0):,.2f} vs {stats.get('prior_avg', 0):,.2f} in the prior 30 "
            f"({trend:+.1f}%)."
        ),
    })
    if anomalies >= 2:
        out.append({
            "metric": m,
            "type": "anomaly_cluster",
            "text": (
                f"{anomalies} anomalies detected in the last 45 days on {m.replace('_', ' ')} — "
                f"pattern suggests {stats.get('anomaly_hint', 'irregular variance')}."
            ),
        })
    if abs(fc) >= 5:
        out.append({
            "metric": m,
            "type": "forecast",
            "text": (
                f"Model projects {m.replace('_', ' ')} to shift {fc:+.1f}% over the forecast "
                f"horizon (confidence-adjusted)."
            ),
        })
    return out


def build_recommendations(all_stats: list[dict]) -> list[Recommendation]:
    """Rank cross-metric stats into prioritized actions."""
    recs: list[Recommendation] = []
    by_metric = {s["metric"]: s for s in all_stats}

    churn = by_metric.get("churn_rate")
    if churn and churn.get("trend_pct", 0) > 3:
        recs.append(Recommendation(
            title="Launch retention sprint on at-risk cohort",
            description=(
                f"Churn rate rose {churn['trend_pct']:+.1f}% (30d vs prior 30d). Stand up win-back "
                "email + in-app check-ins for accounts whose usage dropped >40%."
            ),
            impact="high",
            category="retention",
        ))
    conv = by_metric.get("conversion_rate")
    if conv and conv.get("trend_pct", 0) < -5:
        recs.append(Recommendation(
            title="Audit signup funnel drop-offs",
            description=(
                f"Conversion fell {conv['trend_pct']:+.1f}% recently. Run funnel analytics on "
                "steps 2–3 and A/B test the onboarding CTA copy."
            ),
            impact="high",
            category="growth",
        ))
    cac = by_metric.get("cac")
    if cac and cac.get("trend_pct", 0) > 5:
        recs.append(Recommendation(
            title="Rebalance paid acquisition mix",
            description=(
                f"CAC increased {cac['trend_pct']:+.1f}% without matching volume. Shift 15–20% "
                "budget toward the best organic/referral channel."
            ),
            impact="medium",
            category="efficiency",
        ))
    rev = by_metric.get("revenue")
    if rev and rev.get("trend_pct", 0) > 8:
        recs.append(Recommendation(
            title="Double down on growth drivers",
            description=(
                f"Revenue up {rev['trend_pct']:+.1f}% — lock in the driver (campaign, segment, "
                "pricing test) and scale spend while CAC is favorable."
            ),
            impact="medium",
            category="growth",
        ))
    mrr = by_metric.get("mrr")
    if mrr and mrr.get("forecast_delta_pct", 0) < -2:
        recs.append(Recommendation(
            title="Protect MRR with annual-plan push",
            description=(
                f"Forecast shows MRR {mrr['forecast_delta_pct']:+.1f}% over the horizon. Offer "
                "annual billing discount to high-churn-risk accounts."
            ),
            impact="high",
            category="retention",
        ))
    arpu = by_metric.get("arpu")
    if arpu and arpu.get("trend_pct", 0) > 5:
        recs.append(Recommendation(
            title="Introduce expansion-tier pricing",
            description=(
                f"ARPU climbing {arpu['trend_pct']:+.1f}% suggests willingness to pay. Package a "
                "premium tier with the 2–3 most requested features."
            ),
            impact="low",
            category="growth",
        ))
    new_cust = by_metric.get("new_customers")
    if new_cust and new_cust.get("trend_pct", 0) < -5:
        recs.append(Recommendation(
            title="Investigate acquisition slowdown",
            description=(
                f"New customers fell {new_cust['trend_pct']:+.1f}% over the last 30 days. Review "
                "channel performance and re-activate the top two converting campaigns."
            ),
            impact="medium",
            category="growth",
        ))
    if churn and churn.get("forecast_delta_pct", 0) > 3:
        recs.append(Recommendation(
            title="Pre-empt forecasted churn increase",
            description=(
                f"Model projects churn rising {churn['forecast_delta_pct']:+.1f}% over the next "
                "30 days. Trigger health-score outreach for the bottom-quartile accounts now."
            ),
            impact="high",
            category="retention",
        ))
    if rev and rev.get("forecast_delta_pct", 0) > 5:
        recs.append(Recommendation(
            title="Plan capacity for forecasted revenue growth",
            description=(
                f"Revenue is projected up {rev['forecast_delta_pct']:+.1f}%. Pre-scale support and "
                "infrastructure headcount to protect service quality."
            ),
            impact="medium",
            category="efficiency",
        ))
    if conv and conv.get("forecast_delta_pct", 0) < -3:
        recs.append(Recommendation(
            title="Stabilize conversion before it compounds",
            description=(
                f"Forecast shows conversion continuing down {conv['forecast_delta_pct']:+.1f}%. "
                "Freeze funnel experiments and ship the best-performing control variant."
            ),
            impact="medium",
            category="growth",
        ))
    active = by_metric.get("active_customers")
    if active and active.get("trend_pct", 0) < 1:
        recs.append(Recommendation(
            title="Diagnose growth stall in active base",
            description=(
                f"Active customers grew only {active['trend_pct']:+.1f}% — near flat. Segment "
                "usage cohorts to find where expansion has stopped."
            ),
            impact="low",
            category="retention",
        ))
    cac_anoms = by_metric.get("cac", {}).get("anomalies_recent", 0)
    if cac_anoms >= 2:
        recs.append(Recommendation(
            title="Audit ad-spend anomalies",
            description=(
                f"{cac_anoms} CAC anomalies in 45 days — likely bid-auction volatility or "
                "tracking gaps. Reconcile spend data with platform reports."
            ),
            impact="medium",
            category="data_quality",
        ))
    anomaly_total = sum(s.get("anomalies_recent", 0) for s in all_stats)
    if anomaly_total >= 3:
        recs.append(Recommendation(
            title="Tighten data-pipeline monitoring",
            description=(
                f"{anomaly_total} anomalies across metrics in the last 45 days. Add alerting on "
                "ingest row counts and metric distribution drift."
            ),
            impact="low",
            category="data_quality",
        ))
    if not recs:
        recs.append(Recommendation(
            title="Maintain current strategy",
            description="Metrics are within normal bands — no urgent action. Keep weekly reviews.",
            impact="low",
            category="growth",
        ))
    return recs
