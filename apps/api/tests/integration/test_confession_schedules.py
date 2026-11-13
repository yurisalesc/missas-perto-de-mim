"""Integration tests for confession schedules schema and relations."""

from datetime import time

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.migrations import ensure_confession_schedules_table
from app.models.church import Church
from app.models.confession_schedule import ConfessionSchedule
from app.models.mass_schedule import MassSchedule
from app.services.admin_csv_service import AdminCsvService


@pytest.fixture()
def sqlite_engine():
    """Provide an isolated in-memory SQLite engine."""

    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(sqlite_engine):
    """Provide a session backed by a freshly created schema."""

    Base.metadata.create_all(bind=sqlite_engine)
    SessionLocal = sessionmaker(bind=sqlite_engine, autocommit=False, autoflush=False)
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_confession_schedules_table_mirrors_mass_schedules_schema(sqlite_engine):
    """Ensure confession_schedules mirrors mass_schedules column names and nullability."""

    Base.metadata.create_all(bind=sqlite_engine)
    inspector = inspect(sqlite_engine)

    mass_columns = {col["name"]: col for col in inspector.get_columns("mass_schedules")}
    confession_columns = {col["name"]: col for col in inspector.get_columns("confession_schedules")}

    assert set(mass_columns) == set(confession_columns)
    for name, mass_column in mass_columns.items():
        confession_column = confession_columns[name]
        assert str(confession_column["type"]) == str(mass_column["type"])
        assert confession_column["nullable"] == mass_column["nullable"]

    confession_fks = inspector.get_foreign_keys("confession_schedules")
    assert any(fk["referred_table"] == "churches" and fk["constrained_columns"] == ["church_id"] for fk in confession_fks)


def test_church_exposes_mass_times_and_confession_times_relationships(db_session: Session):
    """Ensure Church uses distinct relationship names for mass and confession schedules."""

    church = Church(
        nome="Paróquia Teste",
        endereco="Rua X",
        cidade="Natal",
        latitude=-5.7945,
        longitude=-35.2110,
    )
    db_session.add(church)
    db_session.flush()

    mass = MassSchedule(
        church_id=church.id,
        dia_semana=0,
        horario=time(19, 0),
        observacao="Missa vespertina",
    )
    confession = ConfessionSchedule(
        church_id=church.id,
        dia_semana=5,
        horario=time(16, 30),
        observacao="Antes da missa",
    )
    db_session.add_all([mass, confession])
    db_session.commit()
    db_session.refresh(church)

    assert len(church.mass_times) == 1
    assert church.mass_times[0].horario == time(19, 0)
    assert len(church.confession_times) == 1
    assert church.confession_times[0].horario == time(16, 30)


def test_ensure_confession_schedules_table_is_additive_and_idempotent(sqlite_engine):
    """Ensure migration creates confession_schedules without removing mass data."""

    with sqlite_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE churches (
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    endereco VARCHAR(255) NOT NULL,
                    cidade VARCHAR(100) NOT NULL,
                    estado VARCHAR(2),
                    latitude FLOAT NOT NULL,
                    longitude FLOAT NOT NULL,
                    telefone VARCHAR(60),
                    redes_sociais_site VARCHAR(255),
                    observacao VARCHAR(255)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE mass_schedules (
                    id INTEGER PRIMARY KEY,
                    church_id INTEGER NOT NULL,
                    dia_semana INTEGER NOT NULL,
                    horario TIME NOT NULL,
                    observacao VARCHAR(255),
                    FOREIGN KEY(church_id) REFERENCES churches (id)
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO churches (id, nome, endereco, cidade, latitude, longitude) "
                "VALUES (1, 'Igreja Antiga', 'Rua Y', 'Natal', -5.79, -35.21)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO mass_schedules (id, church_id, dia_semana, horario, observacao) "
                "VALUES (1, 1, 6, '09:00:00', 'Domingo')"
            )
        )

    assert "confession_schedules" not in inspect(sqlite_engine).get_table_names()

    ensure_confession_schedules_table(sqlite_engine)
    ensure_confession_schedules_table(sqlite_engine)

    inspector = inspect(sqlite_engine)
    assert "confession_schedules" in inspector.get_table_names()
    assert "mass_schedules" in inspector.get_table_names()

    with sqlite_engine.begin() as conn:
        mass_count = conn.execute(text("SELECT COUNT(*) FROM mass_schedules")).scalar_one()
        church_count = conn.execute(text("SELECT COUNT(*) FROM churches")).scalar_one()
        conn.execute(
            text(
                "INSERT INTO confession_schedules (church_id, dia_semana, horario, observacao) "
                "VALUES (1, 5, '16:30:00', 'Confissão')"
            )
        )
        confession_count = conn.execute(text("SELECT COUNT(*) FROM confession_schedules")).scalar_one()

    assert mass_count == 1
    assert church_count == 1
    assert confession_count == 1


def test_deleting_church_cascades_confession_schedules(db_session: Session):
    """Ensure confession schedules are removed with their church via ORM cascade."""

    church = Church(
        nome="Paróquia Cascade",
        endereco="Rua Z",
        cidade="Natal",
        latitude=-5.7945,
        longitude=-35.2110,
    )
    db_session.add(church)
    db_session.flush()
    db_session.add(
        ConfessionSchedule(
            church_id=church.id,
            dia_semana=2,
            horario=time(15, 0),
        )
    )
    db_session.commit()

    confession_id = db_session.query(ConfessionSchedule).one().id
    db_session.delete(church)
    db_session.commit()

    assert db_session.get(ConfessionSchedule, confession_id) is None


def test_csv_replace_reports_deleted_confession_schedules(db_session: Session):
    """Ensure replace import cascades via ORM and reports wiped confession rows."""

    church = Church(
        nome="Paróquia CSV",
        endereco="Rua W",
        cidade="Natal",
        estado="RN",
        latitude=-5.7945,
        longitude=-35.2110,
    )
    db_session.add(church)
    db_session.flush()
    db_session.add_all(
        [
            MassSchedule(church_id=church.id, dia_semana=6, horario=time(9, 0)),
            ConfessionSchedule(church_id=church.id, dia_semana=5, horario=time(16, 0)),
            ConfessionSchedule(church_id=church.id, dia_semana=5, horario=time(17, 0)),
        ]
    )
    db_session.commit()

    csv_content = (
        "Nome da Instituição,Endereço,Cidade,Estado,latitude,longitude,Dom\n"
        "Nova Igreja,Rua Nova,Natal,RN,-5.800000,-35.200000,10:00\n"
    ).encode("utf-8")

    result = AdminCsvService(db_session).populate_database_from_wide_csv(csv_content, replace_existing=True)

    assert result["deleted_confession_schedules"] == 2
    assert result["created_churches"] == 1
    assert result["created_schedules"] == 1
    assert db_session.query(ConfessionSchedule).count() == 0
    assert db_session.query(MassSchedule).count() == 1
