def test_generate_report(client, seeded_db):
    r = client.post("/api/reports/generate?horizon_days=30")
    assert r.status_code == 200
    body = r.json()
    sections = body["sections"]
    assert sections["executive_summary"]
    assert len(sections["key_drivers"]) >= 2
    assert len(sections["risk_factors"]) >= 1
    assert sections["model_accuracy"], "accuracy rows required"
    for row in sections["model_accuracy"]:
        assert {"mae", "rmse", "r2"} <= set(row)
    assert len(sections["next_steps"]) >= 3
    assert all(s["step"] == i + 1 for i, s in enumerate(sections["next_steps"]))
    report_id = body["id"]

    # markdown download
    r2 = client.get(f"/api/reports/{report_id}/markdown")
    assert r2.status_code == 200
    md = r2.text
    for section in ["Executive Summary", "Key Drivers", "Risk Factors", "Model Accuracy", "Strategic Next Steps"]:
        assert section in md
    assert "| Metric | Model | MAE | RMSE | R² |" in md


def test_report_list_and_get(client, seeded_db):
    client.post("/api/reports/generate?horizon_days=30")
    r = client.get("/api/reports")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    rid = items[0]["id"]
    r2 = client.get(f"/api/reports/{rid}")
    assert r2.status_code == 200
    assert r2.json()["sections"]


def test_report_bad_horizon_422(client, seeded_db):
    r = client.post("/api/reports/generate?horizon_days=45")
    assert r.status_code == 422


def test_report_missing_404(client, seeded_db):
    r = client.get("/api/reports/99999")
    assert r.status_code == 404


def test_settings_roundtrip(client, seeded_db):
    r = client.get("/api/settings")
    assert r.status_code == 200
    orig = r.json()

    r2 = client.put("/api/settings", json={"theme": "light", "forecast_days": 90})
    assert r2.status_code == 200
    updated = r2.json()
    assert updated["theme"] == "light"
    assert updated["forecast_days"] == 90

    # invalid theme rejected
    r3 = client.put("/api/settings", json={"theme": "purple"})
    assert r3.status_code == 422

    # restore
    client.put("/api/settings", json={"theme": orig["theme"], "forecast_days": orig["forecast_days"]})
