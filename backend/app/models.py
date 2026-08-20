"""SQLAlchemy models."""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class MetricDaily(Base):
    __tablename__ = "metric_daily"
    __table_args__ = (UniqueConstraint("metric", "date", name="uq_metric_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric: Mapped[str] = mapped_column(String(40), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Numeric(16, 4))


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(12), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rows_processed: Mapped[int] = mapped_column(Integer, default=0)
    stages: Mapped[list] = mapped_column(JSON, default=list)  # [{name,status,duration_ms,rows}]


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(200))
    source_format: Mapped[str] = mapped_column(String(6))
    rows_valid: Mapped[int] = mapped_column(Integer, default=0)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0)
    metric_rows_inserted: Mapped[int] = mapped_column(Integer, default=0)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(120))
    horizon_days: Mapped[int] = mapped_column(Integer)
    content_md: Mapped[str] = mapped_column(Text)
    sections: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    theme: Mapped[str] = mapped_column(String(8), default="dark")
    forecast_days: Mapped[int] = mapped_column(Integer, default=30)
    confidence_level: Mapped[float] = mapped_column(Numeric(4, 2), default=0.80)
    anomaly_sensitivity: Mapped[float] = mapped_column(Numeric(4, 2), default=0.75)
