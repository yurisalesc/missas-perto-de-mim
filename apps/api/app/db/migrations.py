"""Lightweight runtime migrations for additive schema changes."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.models.confession_schedule import ConfessionSchedule


def ensure_church_optional_columns(engine: Engine) -> None:
    """Ensure optional church columns exist and normalize known city labels."""

    inspector = inspect(engine)
    try:
        columns = {col["name"] for col in inspector.get_columns("churches")}
    except Exception:
        return

    desired = {
        "telefone": "VARCHAR(60)",
        "redes_sociais_site": "VARCHAR(255)",
        "observacao": "VARCHAR(255)",
        "estado": "VARCHAR(2)",
    }
    missing = {name: ddl for name, ddl in desired.items() if name not in columns}
    if not missing:
        return

    with engine.begin() as conn:
        for column_name, column_type in missing.items():
            conn.execute(text(f"ALTER TABLE churches ADD COLUMN {column_name} {column_type}"))
        conn.execute(
            text(
                "UPDATE churches SET cidade = 'São Gonçalo do Amarante' "
                "WHERE lower(trim(cidade)) IN ('s. g. amarante', 's.g. amarante', 's g amarante')"
            )
        )


def ensure_confession_schedules_table(engine: Engine) -> None:
    """Explicit additive hook for confession_schedules on existing deployments.

    ``Base.metadata.create_all`` already creates missing tables on startup; this
    helper keeps the confession table creation visible and idempotent for older
    databases that may not reload metadata the same way in scripts/tests.
    """

    Base.metadata.create_all(bind=engine, tables=[ConfessionSchedule.__table__], checkfirst=True)
