import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.seed import generate_series


TEST_DB_URL = "sqlite://"  # in-memory, shared via StaticPool


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()
    yield db
    db.rollback()
    db.close()


@pytest.fixture()
def client(engine, db_session):
    """API client bound to the same in-memory engine."""

    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def sample_series():
    from datetime import date
    return generate_series(240, date.today())


@pytest.fixture()
def seeded_db(engine, db_session, sample_series):
    """Insert a reduced seeded dataset into the test DB (idempotent per test via truncation)."""
    from app.models import MetricDaily, Setting
    db_session.query(MetricDaily).delete()
    db_session.query(Setting).delete()
    rows = []
    for metric, pts in sample_series.items():
        for d, v in pts:
            rows.append(MetricDaily(metric=metric, date=d, value=round(float(v), 4)))
    db_session.add_all(rows)
    if not db_session.query(Setting).filter(Setting.id == 1).count():
        db_session.add(Setting(id=1, theme="dark", forecast_days=30,
                               confidence_level=0.80, anomaly_sensitivity=0.75))
    db_session.commit()
    return db_session
