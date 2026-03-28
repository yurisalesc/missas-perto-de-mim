"""Integration test fixtures."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.church import Church
from app.models.mass_schedule import MassSchedule


@pytest.fixture()
def client():
    """Create API test client with isolated SQLite database."""

    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    church_a = Church(
        nome="Igreja Centro",
        endereco="Rua A",
        cidade="Natal",
        latitude=-5.7945,
        longitude=-35.2110,
    )
    church_b = Church(
        nome="Igreja Distante",
        endereco="Rua B",
        cidade="Natal",
        latitude=-5.8611,
        longitude=-35.2101,
    )
    db.add_all([church_a, church_b])
    db.flush()
    now_local = datetime.now(ZoneInfo("America/Fortaleza")).replace(tzinfo=None)
    near_future = now_local + timedelta(hours=2)
    db.add(
        MassSchedule(
            church_id=church_a.id,
            dia_semana=near_future.weekday(),
            horario=near_future.time().replace(second=0, microsecond=0),
        )
    )
    db.add(
        MassSchedule(
            church_id=church_b.id,
            dia_semana=near_future.weekday(),
            horario=near_future.time().replace(second=0, microsecond=0),
        )
    )
    db.add(
        MassSchedule(
            church_id=church_a.id,
            dia_semana=now_local.weekday(),
            horario=now_local.time().replace(second=0, microsecond=0),
        )
    )
    db.commit()
    db.close()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
