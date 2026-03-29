"""Admin endpoints for CSV import."""

import csv
from datetime import time
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.core.text_normalization import expand_nossa_senhora, normalize_city_name
from app.db.session import get_db
from app.models.church import Church
from app.models.mass_schedule import MassSchedule

router = APIRouter(dependencies=[Depends(require_admin)])

MAX_CSV_SIZE_BYTES = 2 * 1024 * 1024
REQUIRED_COLUMNS = {"nome", "endereco", "cidade", "latitude", "longitude"}


def read_optional(row: dict, *keys: str) -> str | None:
    """Return first non-empty optional value for candidate keys."""

    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text_value = str(value).strip()
        if text_value and text_value != "-":
            return text_value
    return None


@router.post("/importacao/csv")
async def import_churches_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    content = await file.read()
    if len(content) > MAX_CSV_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="CSV file is too large")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV header is required")
    columns = {value.strip() for value in reader.fieldnames if value}
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing CSV columns: {', '.join(missing)}")

    created_churches = 0
    created_schedules = 0
    try:
        for row in reader:
            try:
                church = Church(
                    nome=expand_nossa_senhora(str(row["nome"]).strip()),
                    endereco=str(row["endereco"]).strip(),
                    cidade=normalize_city_name(str(row["cidade"]).strip()),
                    estado=read_optional(row, "estado", "Estado"),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    telefone=read_optional(row, "telefone", "Telefone"),
                    redes_sociais_site=read_optional(
                        row, "redes_sociais_site", "redes sociais/site", "Redes Sociais/Site"
                    ),
                    observacao=read_optional(row, "observacao", "Observação", "flags", "Flags"),
                )
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail="Invalid church row in CSV") from exc

            db.add(church)
            db.flush()
            created_churches += 1

            schedules_raw = (row.get("horarios") or "").strip()
            for token in schedules_raw.split("|"):
                value = token.strip()
                if not value:
                    continue
                try:
                    hours, minutes = value.split(":")
                    schedule = MassSchedule(
                        church_id=church.id,
                        dia_semana=int(row.get("dia_semana", 6)),
                        horario=time(int(hours), int(minutes)),
                        observacao=(row.get("observacao") or None),
                    )
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid schedule row in CSV") from exc
                db.add(schedule)
                created_schedules += 1
        db.commit()
    except HTTPException:
        db.rollback()
        raise

    return {"created_churches": created_churches, "created_schedules": created_schedules}

