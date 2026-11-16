"""Lightweight runtime migrations for additive schema changes."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.models.confession_schedule import ConfessionSchedule

_SQLITE_CREATE_CONFESSION_SCHEDULES = """
CREATE TABLE confession_schedules (
    id INTEGER NOT NULL PRIMARY KEY,
    church_id INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    horario_inicio TIME NOT NULL,
    horario_fim TIME NOT NULL,
    observacao VARCHAR(255),
    FOREIGN KEY(church_id) REFERENCES churches (id)
)
"""


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
    """Ensure confession_schedules exists with inicio/fim range columns.

    Older deployments may still have a single ``horario`` column mirroring mass
    schedules; those rows are migrated to ``horario_inicio``/``horario_fim`` with
    ``horario_fim = horario_inicio + 1 minute`` so ranges remain domain-valid.
    """

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "confession_schedules" not in tables:
        Base.metadata.create_all(bind=engine, tables=[ConfessionSchedule.__table__], checkfirst=True)
        return

    columns = {col["name"] for col in inspector.get_columns("confession_schedules")}
    has_range = "horario_inicio" in columns and "horario_fim" in columns
    has_legacy_point = "horario" in columns
    if has_range and not has_legacy_point:
        return

    dialect = engine.dialect.name
    if dialect == "sqlite":
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE confession_schedules RENAME TO confession_schedules_old"))
            conn.execute(text(_SQLITE_CREATE_CONFESSION_SCHEDULES))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_confession_schedules_church_id ON confession_schedules (church_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_confession_schedules_dia_semana ON confession_schedules (dia_semana)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_confession_schedules_horario_inicio ON confession_schedules (horario_inicio)"))
            if has_legacy_point:
                conn.execute(
                    text(
                        """
                        INSERT INTO confession_schedules
                            (id, church_id, dia_semana, horario_inicio, horario_fim, observacao)
                        SELECT
                            id,
                            church_id,
                            dia_semana,
                            horario,
                            time(horario, '+1 minute'),
                            observacao
                        FROM confession_schedules_old
                        """
                    )
                )
            elif has_range:
                conn.execute(
                    text(
                        """
                        INSERT INTO confession_schedules
                            (id, church_id, dia_semana, horario_inicio, horario_fim, observacao)
                        SELECT id, church_id, dia_semana, horario_inicio, horario_fim, observacao
                        FROM confession_schedules_old
                        """
                    )
                )
            conn.execute(text("DROP TABLE confession_schedules_old"))
        return

    with engine.begin() as conn:
        if "horario_inicio" not in columns:
            conn.execute(text("ALTER TABLE confession_schedules ADD COLUMN horario_inicio TIME"))
        if "horario_fim" not in columns:
            conn.execute(text("ALTER TABLE confession_schedules ADD COLUMN horario_fim TIME"))
        if has_legacy_point:
            conn.execute(
                text(
                    """
                    UPDATE confession_schedules
                    SET horario_inicio = COALESCE(horario_inicio, horario),
                        horario_fim = COALESCE(
                            horario_fim,
                            (COALESCE(horario_inicio, horario) + INTERVAL '1 minute')
                        )
                    WHERE horario IS NOT NULL
                    """
                )
            )
            conn.execute(text("ALTER TABLE confession_schedules ALTER COLUMN horario_inicio SET NOT NULL"))
            conn.execute(text("ALTER TABLE confession_schedules ALTER COLUMN horario_fim SET NOT NULL"))
            conn.execute(text("ALTER TABLE confession_schedules DROP COLUMN horario"))
