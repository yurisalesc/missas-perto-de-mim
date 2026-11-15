"""Integration tests for admin suggestions/changelog pagination and legacy lists."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.changelog import ChangelogBadge, ChangelogEntry
from app.models.suggestion import UserSuggestion


@pytest.fixture()
def admin_client(monkeypatch):
    """Authenticated admin client with seeded suggestions and changelog."""

    monkeypatch.setattr(settings, "admin_password", "secret")
    monkeypatch.setattr(settings, "admin_password_hash", None)
    monkeypatch.setattr(settings, "app_env", "development")

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
    now = datetime(2026, 1, 10, 12, 0, 0)
    for index in range(3):
        db.add(
            UserSuggestion(
                nome_igreja=f"Igreja {index}",
                endereco=f"Rua {index}",
                cidade="Natal",
                mensagem=f"Msg {index}",
                status="pending",
            )
        )
        db.add(
            ChangelogEntry(
                title=f"Update {index}",
                description=f"Desc {index}",
                badge=ChangelogBadge.NEW,
                published_at=now,
            )
        )
    db.commit()
    db.close()

    with TestClient(app) as test_client:
        test_client.auth = ("admin", "secret")
        yield test_client

    app.dependency_overrides.clear()


def test_suggestions_paginated(admin_client):
    response = admin_client.get("/admin/sugestoes", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert len(payload["items"]) == 2


def test_suggestions_legacy_list(admin_client):
    response = admin_client.get("/admin/sugestoes")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 3


def test_changelog_paginated(admin_client):
    response = admin_client.get("/admin/changelog", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert len(payload["items"]) == 2


def test_changelog_legacy_list(admin_client):
    response = admin_client.get("/admin/changelog")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 3
