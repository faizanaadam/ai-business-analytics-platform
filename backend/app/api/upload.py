"""Upload endpoint: CSV/JSON → validate → ingest."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..etl.validator import validate_payload
from ..etl.ingest import ingest_records
from ..models import Upload

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    upload_id: int
    filename: str
    format: str
    rows_valid: int
    rows_rejected: int
    metric_rows_inserted: int
    errors: list[dict]


MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("", response_model=UploadResponse)
async def upload_data(
    file: UploadFile = File(...),
    source_format: str = Form("auto"),
    db: Session = Depends(get_db),
):
    filename = file.filename or "upload"
    size = 0
    chunks = []
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(422, f"file too large (max {MAX_UPLOAD_BYTES // (1024*1024)} MB)")
        chunks.append(chunk)
    raw = b"".join(chunks)
    if not raw:
        raise HTTPException(422, "empty file")
    if source_format == "auto":
        source_format = "json" if filename.lower().endswith(".json") else "csv"

    try:
        report = validate_payload(raw, source_format)
    except ValueError as e:
        raise HTTPException(422, str(e))

    inserted = ingest_records(db, report.records)

    up = Upload(
        filename=filename, source_format=source_format,
        rows_valid=report.rows_valid, rows_rejected=report.rows_rejected,
        metric_rows_inserted=inserted, validation_errors=report.errors[:200],
        created_at=datetime.utcnow(),
    )
    db.add(up)
    db.commit()
    db.refresh(up)

    return UploadResponse(
        upload_id=up.id, filename=filename, format=source_format,
        rows_valid=report.rows_valid, rows_rejected=report.rows_rejected,
        metric_rows_inserted=inserted, errors=report.errors[:50],
    )
