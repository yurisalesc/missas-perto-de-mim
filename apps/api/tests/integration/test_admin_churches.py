"""Integration tests for admin church CRUD with nested schedules."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.church import Church


@pytest.fixture()
def admin_client(monkeypatch):
    """Authenticated admin client with isolated DB."""

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
    for index in range(3):
        db.add(
            Church(
                nome=f"Igreja {index}",
                endereco=f"Rua {index}",
                cidade="Natal" if index < 2 else "Parnamirim",
                estado="RN",
                latitude=-5.79,
                longitude=-35.21,
            )
        )
    db.commit()
    db.close()

    with TestClient(app) as test_client:
        test_client.auth = ("admin", "secret")
        yield test_client

    app.dependency_overrides.clear()


def test_list_churches_is_paginated(admin_client):
    response = admin_client.get("/admin/igrejas", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert len(payload["items"]) == 2


def test_list_churches_without_pagination_returns_legacy_list(admin_client):
    response = admin_client.get("/admin/igrejas")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 3


def test_rejects_invalid_estado(admin_client):
    response = admin_client.post(
        "/admin/igrejas",
        json={
            "nome": "Paróquia UF",
            "endereco": "Rua UF",
            "cidade": "Natal",
            "estado": "R1",
            "latitude": -5.8,
            "longitude": -35.2,
        },
    )
    assert response.status_code == 422


def test_create_church_with_nested_schedules(admin_client):
    response = admin_client.post(
        "/admin/igrejas",
        json={
            "nome": "Paróquia Nova",
            "endereco": "Rua Nova, 100",
            "cidade": "Natal",
            "estado": "rn",
            "latitude": -5.8,
            "longitude": -35.2,
            "mass_times": [{"dia_semana": 6, "horario": "10:00:00"}],
            "confession_times": [
                {
                    "dia_semana": 5,
                    "horario_inicio": "15:00:00",
                    "horario_fim": "17:00:00",
                }
            ],
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["estado"] == "RN"
    assert len(payload["mass_times"]) == 1
    assert payload["mass_times"][0]["horario"] == "10:00:00"
    assert len(payload["confession_times"]) == 1
    assert payload["confession_times"][0]["horario_inicio"] == "15:00:00"
    assert payload["confession_times"][0]["horario_fim"] == "17:00:00"


def test_get_and_replace_schedules(admin_client):
    created = admin_client.post(
        "/admin/igrejas",
        json={
            "nome": "Paróquia Edit",
            "endereco": "Rua Edit",
            "cidade": "Natal",
            "latitude": -5.8,
            "longitude": -35.2,
            "mass_times": [{"dia_semana": 0, "horario": "19:00:00"}],
            "confession_times": [
                {
                    "dia_semana": 5,
                    "horario_inicio": "15:00:00",
                    "horario_fim": "16:00:00",
                }
            ],
        },
    ).json()

    detail = admin_client.get(f"/admin/igrejas/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["nome"] == "Paróquia Edit"

    updated = admin_client.patch(
        f"/admin/igrejas/{created['id']}",
        json={
            "mass_times": [
                {"dia_semana": 6, "horario": "08:00:00"},
                {"dia_semana": 6, "horario": "18:00:00"},
            ],
            "confession_times": [
                {
                    "dia_semana": 4,
                    "horario_inicio": "14:30:00",
                    "horario_fim": "16:30:00",
                }
            ],
        },
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert len(payload["mass_times"]) == 2
    assert len(payload["confession_times"]) == 1
    assert payload["confession_times"][0]["horario_inicio"] == "14:30:00"


def test_rejects_invalid_confession_range(admin_client):
    response = admin_client.post(
        "/admin/igrejas",
        json={
            "nome": "Paróquia Bad",
            "endereco": "Rua Bad",
            "cidade": "Natal",
            "latitude": -5.8,
            "longitude": -35.2,
            "confession_times": [
                {
                    "dia_semana": 5,
                    "horario_inicio": "17:00:00",
                    "horario_fim": "15:00:00",
                }
            ],
        },
    )
    assert response.status_code == 422
