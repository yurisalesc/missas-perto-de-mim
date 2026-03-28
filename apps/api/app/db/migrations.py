"""Lightweight runtime migrations for additive schema changes."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_church_contact_columns(engine: Engine) -> None:
    """Ensure optional contact columns exist on churches table."""

    inspector = inspect(engine)
    try:
        columns = {col["name"] for col in inspector.get_columns("churches")}
    except Exception:
        return

    desired = {
        "telefone": "VARCHAR(60)",
        "redes_sociais_site": "VARCHAR(255)",
        "observacao": "VARCHAR(255)",
    }
    missing = {name: ddl for name, ddl in desired.items() if name not in columns}
    if not missing:
        return

    with engine.begin() as conn:
        for column_name, column_type in missing.items():
            conn.execute(text(f"ALTER TABLE churches ADD COLUMN {column_name} {column_type}"))
