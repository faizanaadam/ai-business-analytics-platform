"""Upload schema validation for CSV/JSON business data.

Accepted schema (either long or wide):
  long:  date, metric, value
  wide:  date, revenue, mrr, churn_rate, cac, new_customers, conversion_rate,
         active_customers, arpu  (any non-empty subset)
"""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime
from typing import Any

KNOWN_METRICS = {
    "revenue", "mrr", "churn_rate", "cac", "new_customers",
    "conversion_rate", "active_customers", "arpu",
}

MAX_ROWS = 50_000


class ValidationReport:
    def __init__(self) -> None:
        self.rows_valid = 0
        self.rows_rejected = 0
        self.errors: list[dict] = []
        self.records: list[tuple[date, str, float]] = []

    def error(self, row: int, field: str, message: str) -> None:
        self.errors.append({"row": row, "field": field, "message": message})
        self.rows_rejected += 1


def _parse_date(raw: Any) -> date | None:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except ValueError:
            continue
    return None


def _parse_value(raw: Any) -> float | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(",", "").replace("$", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def validate_payload(payload: bytes | str, source_format: str) -> ValidationReport:
    """Parse + validate. Raises ValueError on unreadable structure / bad schema."""
    report = ValidationReport()
    if source_format == "json":
        rows = json.loads(payload if isinstance(payload, str) else payload.decode("utf-8"))
        if isinstance(rows, dict):
            rows = rows.get("data", rows.get("records", rows.get("rows")))
            if not isinstance(rows, list):
                raise ValueError("JSON must be an array of records (or {data: [...]})")
        _validate_rows(rows, report, start_row=1)
        return report
    if source_format == "csv":
        text = payload.decode("utf-8-sig") if isinstance(payload, bytes) else payload
        try:
            reader = csv.DictReader(io.StringIO(text))
            if reader.fieldnames is None:
                raise ValueError("CSV has no header row")
            rows = list(reader)
        except csv.Error as e:  # e.g. field larger than field limit, malformed rows
            raise ValueError(f"unreadable CSV: {e}") from e
        _validate_rows(rows, report, start_row=2)  # row 1 is the header
        return report
    raise ValueError(f"unsupported format {source_format!r}")


def _validate_rows(rows: list, report: ValidationReport, start_row: int) -> None:
    if len(rows) > MAX_ROWS:
        raise ValueError(f"too many rows: {len(rows)} > {MAX_ROWS}")
    if not rows:
        raise ValueError("no data rows found")
    if not isinstance(rows[0], dict):
        raise ValueError("each record must be an object")
    fields = [str(f).strip() for f in rows[0].keys()]
    lower = [f.lower() for f in fields]
    metric_cols = [c for c in lower if c not in ("date",) and c in KNOWN_METRICS]
    is_long = "metric" in lower and "value" in lower and "date" in lower
    is_wide = "date" in lower and len(metric_cols) >= 1

    if not (is_long or is_wide):
        raise ValueError(
            "schema mismatch: need columns [date, metric, value] (long) or "
            "[date, revenue, mrr, ...] (wide) with at least one known metric"
        )

    for i, row in enumerate(rows):
        row_no = start_row + i
        d = _parse_date(row.get("date"))
        if d is None:
            report.error(row_no, "date", f"unparseable date {row.get('date')!r}")
            continue
        if is_long:
            m = str(row.get("metric", "")).strip().lower()
            if m not in KNOWN_METRICS:
                report.error(row_no, "metric", f"unknown metric {m!r}")
                continue
            v = _parse_value(row.get("value"))
            if v is None:
                report.error(row_no, "value", f"non-numeric value {row.get('value')!r}")
                continue
            report.records.append((d, m, v))
            report.rows_valid += 1
        else:
            added = 0
            for col in fields:
                lc = col.lower()
                if lc in ("date", "", "metric", "value"):
                    continue
                if lc not in KNOWN_METRICS:
                    continue
                raw = row.get(col)
                if raw is None or str(raw).strip() == "":
                    continue
                v = _parse_value(raw)
                if v is None:
                    report.error(row_no, lc, f"non-numeric {raw!r}")
                    continue
                report.records.append((d, lc, v))
                added += 1
            if added:
                report.rows_valid += 1
