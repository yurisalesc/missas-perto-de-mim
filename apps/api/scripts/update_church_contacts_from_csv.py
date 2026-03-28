"""Update church contact fields from a source CSV file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sqlalchemy import text

from app.core.text_normalization import expand_nossa_senhora, normalize_search_token
from app.db.session import SessionLocal, engine
from app.models.church import Church


def ensure_columns() -> None:
    """Add optional church columns when they are missing."""

    with engine.begin() as conn:
        existing = {
            row[1] for row in conn.execute(text("PRAGMA table_info(churches)")).fetchall()
        } if engine.dialect.name == "sqlite" else {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'churches'"
                )
            ).fetchall()
        }
        for name, ddl in (
            ("telefone", "VARCHAR(60)"),
            ("redes_sociais_site", "VARCHAR(255)"),
            ("observacao", "VARCHAR(255)"),
        ):
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE churches ADD COLUMN {name} {ddl}"))


def normalize_name(value: str) -> str:
    """Normalize a church name for robust matching."""

    return normalize_search_token(expand_nossa_senhora((value or "").strip()))


def normalize_city(value: str) -> str:
    """Normalize a city value for robust matching."""

    return normalize_search_token((value or "").strip())


def clean_optional(value: str | None) -> str | None:
    """Convert CSV placeholders to null."""

    text_value = (value or "").strip()
    if not text_value or text_value == "-":
        return None
    return text_value


def choose_row(rows: list[dict], church_name: str, church_city: str) -> dict | None:
    """Pick best row for a church using normalized name/city matching."""

    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]

    normalized_city = normalize_city(church_city)
    city_matches = [
        row
        for row in rows
        if normalize_city(row.get("Cidade", "")) == normalized_city
        or normalize_city(row.get("Cidade", "")) in normalized_city
        or normalized_city in normalize_city(row.get("Cidade", ""))
    ]
    if len(city_matches) == 1:
        return city_matches[0]
    if city_matches:
        rows = city_matches

    normalized_name = normalize_name(church_name)
    for row in rows:
        row_name = normalize_name(row.get("Nome da Instituição", ""))
        if row_name == normalized_name:
            return row
    for row in rows:
        row_name = normalize_name(row.get("Nome da Instituição", ""))
        if row_name in normalized_name or normalized_name in row_name:
            return row
    return rows[0]


def run(csv_path: Path) -> None:
    """Apply contact data from CSV into existing churches."""

    ensure_columns()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    rows_by_name: dict[str, list[dict]] = {}
    for row in rows:
        key = normalize_name(row.get("Nome da Instituição", ""))
        if not key:
            continue
        rows_by_name.setdefault(key, []).append(row)

    db = SessionLocal()
    try:
        churches = db.query(Church).all()
        updated = 0
        not_matched = 0
        for church in churches:
            normalized_name = normalize_name(church.nome)
            candidates = rows_by_name.get(normalized_name, [])
            if not candidates:
                not_matched += 1
                continue
            row = choose_row(candidates, church.nome, church.cidade)
            if not row:
                not_matched += 1
                continue

            church.telefone = clean_optional(row.get("Telefone"))
            church.redes_sociais_site = clean_optional(row.get("Redes Sociais/Site"))
            church.observacao = clean_optional(row.get("Flags"))
            updated += 1

        db.commit()
        print(f"updated={updated} not_matched={not_matched}")
    finally:
        db.close()


def main() -> None:
    """Parse args and run update."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="/home/yuriscosta/Downloads/convertcsv (2).csv",
        help="Absolute path to source CSV",
    )
    args = parser.parse_args()
    run(Path(args.csv))


if __name__ == "__main__":
    main()
