import pytest

from app.etl.validator import validate_payload


def test_valid_long_csv():
    csv = "date,metric,value\n2026-01-01,revenue,1000.5\n2026-01-02,mrr,42000\n"
    r = validate_payload(csv, "csv")
    assert r.rows_valid == 2
    assert r.rows_rejected == 0
    assert len(r.records) == 2


def test_valid_wide_csv():
    csv = "date,revenue,mrr\n2026-01-01,1000,42000\n2026-01-02,1100,42500\n"
    r = validate_payload(csv, "csv")
    assert r.rows_valid == 2
    assert r.rows_rejected == 0
    assert len(r.records) == 4


def test_csv_with_currency_commas():
    csv = "date,metric,value\n2026-01-01,revenue,\"$1,200.50\"\n"
    r = validate_payload(csv, "csv")
    assert r.rows_valid == 1
    assert r.records[0][2] == 1200.50


def test_invalid_schema_rejected():
    with pytest.raises(ValueError, match="schema mismatch"):
        validate_payload("a,b,c\n1,2,3\n", "csv")


def test_missing_header_rejected():
    with pytest.raises(ValueError):
        validate_payload("just some text\nno header", "csv")


def test_row_errors_counted():
    csv = "date,metric,value\n2026-01-01,revenue,abc\n2026-13-99,revenue,10\n2026-01-03,revenue,15\n"
    r = validate_payload(csv, "csv")
    assert r.rows_valid == 1
    assert r.rows_rejected == 2
    assert len(r.errors) == 2


def test_json_long_format():
    import json
    payload = json.dumps([
        {"date": "2026-01-01", "metric": "revenue", "value": 990.0},
        {"date": "2026-01-02", "metric": "churn_rate", "value": 3.1},
    ])
    r = validate_payload(payload, "json")
    assert r.rows_valid == 2
    assert r.rows_rejected == 0


def test_json_wide_with_data_wrapper():
    import json
    payload = json.dumps({"data": [{"date": "2026-01-01", "revenue": 1000, "cac": 95}]})
    r = validate_payload(payload, "json")
    assert r.rows_valid == 1
    assert r.records[0] == (r.records[0][0], "revenue", 1000.0)


def test_unknown_metric_rejected():
    csv = "date,metric,value\n2026-01-01,happiness,10\n"
    r = validate_payload(csv, "csv")
    assert r.rows_valid == 0
    assert r.rows_rejected == 1


def test_empty_rows_rejected():
    with pytest.raises(ValueError, match="no data rows"):
        validate_payload("date,metric,value\n", "csv")


def test_unsupported_format():
    with pytest.raises(ValueError):
        validate_payload("x", "xml")
