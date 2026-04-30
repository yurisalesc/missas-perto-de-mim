"""Integration tests for the public changelog endpoint."""

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
from app.models.changelog import ChangelogBadge, ChangelogEntry

_FORTALEZA_TZ = ZoneInfo("America/Fortaleza")


@pytest.fixture()
def changelog_client():
    """Test client with isolated DB seeded with changelog entries."""

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

    now_local = datetime.now(_FORTALEZA_TZ).replace(tzinfo=None)
    db = TestingSessionLocal()
    db.add_all(
        [
            ChangelogEntry(
                title="Recent entry",
                description="Published 5 days ago",
                badge=ChangelogBadge.NEW,
                published_at=now_local - timedelta(days=5),
            ),
            ChangelogEntry(
                title="Older entry",
                description="Published 10 days ago",
                badge=ChangelogBadge.IMPROVED,
                published_at=now_local - timedelta(days=10),
            ),
            ChangelogEntry(
                title="Too old entry",
                description="Published 20 days ago — outside 15-day window",
                badge=ChangelogBadge.FIXED,
                published_at=now_local - timedelta(days=20),
            ),
        ]
    )
    db.commit()
    db.close()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_latest_returns_only_last_15_days(changelog_client):
    """Entries older than 15 days must not appear in /changelog/latest."""

    response = changelog_client.get("/changelog/latest")
    assert response.status_code == 200
    titles = [entry["title"] for entry in response.json()]
    assert "Recent entry" in titles
    assert "Older entry" in titles
    assert "Too old entry" not in titles


def test_latest_returns_entries_in_descending_order(changelog_client):
    """Entries must be returned newest-first."""

    response = changelog_client.get("/changelog/latest")
    assert response.status_code == 200
    entries = response.json()
    dates = [entry["published_at"] for entry in entries]
    assert dates == sorted(dates, reverse=True)
