import json

from app.models import MetricDaily


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_kpis(client, seeded_db):
    r = client.get("/api/kpis")
    assert r.status_code == 200
    cards = r.json()
    keys = {c["key"] for c in cards}
    assert {"revenue", "cac", "churn_rate", "mrr", "projected_growth"} <= keys
    for c in cards:
        assert c["direction"] in {"up", "down", "flat"}
        assert c["good_direction"] in {"up", "down"}
        assert isinstance(c["value"], (int, float))


def test_forecast_endpoint(client, seeded_db):
    r = client.post("/api/forecast", json={"metric": "revenue", "days": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["metric"] == "revenue"
    assert len(body["forecast"]) == 30
    assert body["history"], "history must be non-empty"
    for p in body["forecast"]:
        assert p["lower95"] <= p["lower80"] <= p["value"] <= p["upper80"] <= p["upper95"]
    assert set(body["accuracy"]) == {"mae", "rmse", "r2"}


def test_forecast_unknown_metric_404(client, seeded_db):
    r = client.post("/api/forecast", json={"metric": "nope", "days": 30})
    assert r.status_code == 404


def test_forecast_bad_days_422(client, seeded_db):
    r = client.post("/api/forecast", json={"metric": "revenue", "days": 45})
    assert r.status_code == 422


def test_anomalies_endpoint(client, seeded_db):
    r = client.get("/api/anomalies")
    assert r.status_code == 200
    anoms = r.json()
    assert len(anoms) >= 3, "seeded anomalies should surface"
    assert all(a["severity"] in {"high", "medium", "low"} for a in anoms)
    # severity sorted high first
    order = {"high": 0, "medium": 1, "low": 2}
    seq = [order[a["severity"]] for a in anoms]
    assert seq == sorted(seq)


def test_recommendations_endpoint(client, seeded_db):
    r = client.get("/api/recommendations")
    assert r.status_code == 200
    body = r.json()
    assert len(body["recommendations"]) >= 4
    impacts = {rec["impact"] for rec in body["recommendations"]}
    assert impacts <= {"high", "medium", "low"}
    order = {"high": 0, "medium": 1, "low": 2}
    seq = [order[rec["impact"]] for rec in body["recommendations"]]
    assert seq == sorted(seq)


def test_metrics_list_and_history(client, seeded_db):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    metrics = r.json()
    assert len(metrics) == 8
    r2 = client.get("/api/metrics/revenue/history?days=30")
    assert r2.status_code == 200
    assert 28 <= len(r2.json()) <= 30


def test_history_unknown_404(client, seeded_db):
    r = client.get("/api/metrics/nope/history")
    assert r.status_code == 404
