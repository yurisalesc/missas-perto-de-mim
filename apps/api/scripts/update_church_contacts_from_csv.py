"""Update church contact fields from a source CSV file."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import time
from pathlib import Path

from sqlalchemy import text

from app.core.text_normalization import expand_nossa_senhora, normalize_city_name, normalize_search_token
from app.db.session import SessionLocal, engine
from app.models.church import Church
from app.models.mass_schedule import MassSchedule


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


def normalize_coordinate(raw: str | None, *, is_latitude: bool) -> float | None:
    """Normalize malformed coordinate values from CSV sources."""

    value = clean_optional(raw)
    if not value:
        return None
    normalized = value.replace(",", ".")
    try:
        number = float(normalized)
    except ValueError:
        return None

    # Handles values like -57.877 and -352.045 that should be -5.7877 and -35.2045.
    if is_latitude:
        while abs(number) > 9:
            number /= 10.0
        if not (-90 <= number <= 90):
            return None
    else:
        while abs(number) > 90:
            number /= 10.0
        if not (-180 <= number <= 180):
            return None
    return number


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


def parse_day_times(raw: str | None) -> list[time]:
    """Extract HH:MM times from free text cells."""

    value = clean_optional(raw)
    if not value:
        return []
    result: list[time] = []
    for hours_text, minutes_text in re.findall(r"(\d{1,2}):(\d{2})", value):
        hours = int(hours_text)
        minutes = int(minutes_text)
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            result.append(time(hours, minutes))
    return result


def create_missing_church_from_row(db, row: dict) -> bool:
    """Create a church and weekly schedules from CSV row when absent."""

    name = expand_nossa_senhora((row.get("Nome da Instituição") or "").strip())
    address = (row.get("Endereço") or "").strip()
    city = normalize_city_name((row.get("Cidade") or "").strip())
    latitude = normalize_coordinate(row.get("latitude"), is_latitude=True)
    longitude = normalize_coordinate(row.get("longitude"), is_latitude=False)

    if not name or not address or not city or latitude is None or longitude is None:
        return False

    church = Church(
        nome=name,
        endereco=address,
        cidade=city,
        estado=clean_optional(row.get("Estado")),
        latitude=latitude,
        longitude=longitude,
        telefone=clean_optional(row.get("Telefone")),
        redes_sociais_site=clean_optional(row.get("Redes Sociais/Site")),
        observacao=clean_optional(row.get("Flags")),
    )
    db.add(church)
    db.flush()

    day_columns = [
        ("Seg", 0),
        ("Ter", 1),
        ("Qua", 2),
        ("Qui", 3),
        ("Sex", 4),
        ("Sab", 5),
        ("Dom", 6),
    ]
    for column_name, weekday in day_columns:
        for schedule_time in parse_day_times(row.get(column_name)):
            db.add(
                MassSchedule(
                    church_id=church.id,
                    dia_semana=weekday,
                    horario=schedule_time,
                    observacao=clean_optional(row.get("Flags")),
                )
            )
    return True


def run(csv_path: Path) -> None:
    """Apply contact/coordinates updates and create missing churches from CSV."""

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
        created = 0
        used_rows: set[int] = set()
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
            for idx, candidate in enumerate(rows):
                if candidate is row:
                    used_rows.add(idx)
                    break

            church.telefone = clean_optional(row.get("Telefone"))
            church.redes_sociais_site = clean_optional(row.get("Redes Sociais/Site"))
            church.observacao = clean_optional(row.get("Flags"))
            church.cidade = normalize_city_name(church.cidade)
            church.estado = clean_optional(row.get("Estado")) or church.estado or "RN"
            parsed_lat = normalize_coordinate(row.get("latitude"), is_latitude=True)
            parsed_lon = normalize_coordinate(row.get("longitude"), is_latitude=False)
            if parsed_lat is not None and parsed_lon is not None:
                church.latitude = parsed_lat
                church.longitude = parsed_lon
            updated += 1

        for idx, row in enumerate(rows):
            if idx in used_rows:
                continue
            if create_missing_church_from_row(db, row):
                created += 1

        db.commit()
        print(f"updated={updated} created={created} not_matched={not_matched}")
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
