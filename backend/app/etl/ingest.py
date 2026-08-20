"""Ingestion: validated records → metric_daily (last-write-wins on duplicates)."""
from __future__ import annotations

from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from ..models import MetricDaily


def ingest_records(db: Session, records: list[tuple]) -> int:
    """records: [(date, metric, value)] — upsert into metric_daily."""
    if not records:
        return 0
    # de-dup within batch (last wins)
    dedup: dict[tuple, float] = {}
    for d, m, v in records:
        dedup[(d, m)] = float(v)

    rows = [{"metric": m, "date": d, "value": v} for (d, m), v in dedup.items()]

    bind = db.get_bind()
    if bind.dialect.name == "mysql":
        stmt = mysql_insert(MetricDaily).values(rows)
        stmt = stmt.on_duplicate_key_update(value=stmt.inserted.value)
        db.execute(stmt)
    else:  # sqlite (tests)
        db.execute(
            sa_text(
                "INSERT INTO metric_daily (metric, date, value) VALUES (:metric, :date, :value) "
                "ON CONFLICT(metric, date) DO UPDATE SET value = excluded.value"
            ),
            rows,
        )
    db.commit()
    return len(rows)
