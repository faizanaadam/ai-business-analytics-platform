def test_upload_long_csv(client, seeded_db):
    csv = "date,metric,value\n2026-07-01,revenue,9000\n2026-07-02,revenue,9100\n"
    r = client.post("/api/upload", files={"file": ("data.csv", csv.encode(), "text/csv")},
                    data={"source_format": "auto"})
    assert r.status_code == 200
    body = r.json()
    assert body["rows_valid"] == 2
    assert body["metric_rows_inserted"] == 2
    assert body["rows_rejected"] == 0


def test_upload_invalid_schema_422(client, seeded_db):
    csv = "foo,bar\n1,2\n"
    r = client.post("/api/upload", files={"file": ("bad.csv", csv.encode(), "text/csv")},
                    data={"source_format": "auto"})
    assert r.status_code == 422
    assert "schema" in r.json()["detail"].lower()


def test_upload_row_level_errors_reported(client, seeded_db):
    csv = "date,metric,value\n2026-07-01,revenue,ok-not-a-number\n2026-07-02,revenue,100\n"
    r = client.post("/api/upload", files={"file": ("data.csv", csv.encode(), "text/csv")},
                    data={"source_format": "auto"})
    assert r.status_code == 200
    body = r.json()
    assert body["rows_valid"] == 1
    assert body["rows_rejected"] == 1
    assert body["errors"][0]["field"] == "value"


def test_upload_json(client, seeded_db):
    import json
    payload = json.dumps({"data": [{"date": "2026-07-01", "revenue": 5000, "mrr": 40000}]})
    r = client.post("/api/upload", files={"file": ("d.json", payload.encode(), "application/json")},
                    data={"source_format": "auto"})
    assert r.status_code == 200
    assert r.json()["metric_rows_inserted"] == 2


def test_upload_empty_file_422(client, seeded_db):
    r = client.post("/api/upload", files={"file": ("e.csv", b"", "text/csv")},
                    data={"source_format": "auto"})
    assert r.status_code == 422


def test_pipeline_runs_list_and_run(client, seeded_db):
    # seed historical runs WITHOUT a `rows` key in stages — regression test:
    # seeded rows must serialize even when stage dicts lack optional fields
    from datetime import datetime
    from app.models import PipelineRun
    seeded_db.add(PipelineRun(
        job_name="extract_transactions", status="success",
        started_at=datetime(2026, 8, 19, 10, 0), finished_at=datetime(2026, 8, 19, 10, 0, 12),
        rows_processed=48210,
        stages=[{"name": "extract", "status": "success", "duration_ms": 2600}],
    ))
    seeded_db.commit()

    r = client.get("/api/pipeline/runs")
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) >= 1
    # seeded run without a `rows` key must serialize with rows=0 default
    seeded = next(run for run in runs if run["job_name"] == "extract_transactions")
    assert seeded["stages"][0]["rows"] == 0

    r2 = client.post("/api/pipeline/run")
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] in {"success", "failed"}
    assert len(body["stages"]) >= 1
    assert all(s["status"] in {"success", "failed", "skipped"} for s in body["stages"])

    r3 = client.get("/api/pipeline/freshness")
    assert r3.status_code == 200
    f = r3.json()
    assert f["latest_data_date"] is not None
    assert f["is_fresh"] in (True, False)
    assert f["last_pipeline_at"] is not None


def test_pipeline_freshness_empty_runs(client, db_session):
    from app.models import PipelineRun
    db_session.query(PipelineRun).delete()
    db_session.commit()
    r = client.get("/api/pipeline/freshness")
    assert r.status_code == 200
    assert r.json()["last_pipeline_at"] is None
