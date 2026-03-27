"""Admin endpoints for CRUD, moderation and import."""

import csv
from datetime import time
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.models.church import Church
from app.models.mass_schedule import MassSchedule
from app.repositories.church_repository import ChurchRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.church import ChurchCreate, ChurchOut, ChurchUpdate
from app.schemas.mass_schedule import MassScheduleCreate, MassScheduleOut, MassScheduleUpdate
from app.schemas.suggestion import SuggestionModeration, SuggestionOut

router = APIRouter(tags=["administracao"], dependencies=[Depends(require_admin)])


@router.post("/igrejas", response_model=ChurchOut, status_code=201)
def create_church(payload: ChurchCreate, db: Session = Depends(get_db)) -> Church:
    """Create church entity."""

    return ChurchRepository(db).create(Church(**payload.model_dump()))


@router.get("/igrejas", response_model=list[ChurchOut])
def list_churches(db: Session = Depends(get_db)) -> list[Church]:
    """List all churches."""

    return ChurchRepository(db).list_with_schedules()


@router.patch("/igrejas/{church_id}", response_model=ChurchOut)
def update_church(church_id: int, payload: ChurchUpdate, db: Session = Depends(get_db)) -> Church:
    """Update a church entity."""

    church = ChurchRepository(db).get(church_id)
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(church, key, value)
    db.commit()
    db.refresh(church)
    return church


@router.delete("/igrejas/{church_id}", status_code=204)
def delete_church(church_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a church entity."""

    church = ChurchRepository(db).get(church_id)
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    ChurchRepository(db).delete(church)


@router.post("/horarios", response_model=MassScheduleOut, status_code=201)
def create_schedule(payload: MassScheduleCreate, db: Session = Depends(get_db)) -> MassSchedule:
    """Create mass schedule entity."""

    church = ChurchRepository(db).get(payload.church_id)
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return ScheduleRepository(db).create(MassSchedule(**payload.model_dump()))


@router.get("/horarios", response_model=list[MassScheduleOut])
def list_schedules(db: Session = Depends(get_db)) -> list[MassSchedule]:
    """List all mass schedules."""

    return ScheduleRepository(db).list_all()


@router.patch("/horarios/{schedule_id}", response_model=MassScheduleOut)
def update_schedule(schedule_id: int, payload: MassScheduleUpdate, db: Session = Depends(get_db)) -> MassSchedule:
    """Update a mass schedule entity."""

    schedule = ScheduleRepository(db).get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    data = payload.model_dump(exclude_none=True)
    if "church_id" in data and not ChurchRepository(db).get(data["church_id"]):
        raise HTTPException(status_code=404, detail="Church not found")
    for key, value in data.items():
        setattr(schedule, key, value)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/horarios/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a mass schedule entity."""

    schedule = ScheduleRepository(db).get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    ScheduleRepository(db).delete(schedule)


@router.get("/sugestoes", response_model=list[SuggestionOut])
def list_suggestions(db: Session = Depends(get_db)):
    """List all user suggestions for moderation."""

    return SuggestionRepository(db).list_all()


@router.patch("/sugestoes/{suggestion_id}", response_model=SuggestionOut)
def moderate_suggestion(
    suggestion_id: int, payload: SuggestionModeration, db: Session = Depends(get_db)
):
    """Approve or reject a user suggestion."""

    suggestion = SuggestionRepository(db).get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = payload.status
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.post("/importacao/csv")
async def import_churches_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    """Import churches and schedules from a CSV file."""

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(StringIO(text))
    created_churches = 0
    created_schedules = 0

    for row in reader:
        church = Church(
            nome=row["nome"],
            endereco=row["endereco"],
            cidade=row["cidade"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        db.add(church)
        db.flush()
        created_churches += 1
        schedules_raw = row.get("horarios", "")
        for token in schedules_raw.split("|"):
            value = token.strip()
            if not value:
                continue
            hours, minutes = value.split(":")
            schedule = MassSchedule(
                church_id=church.id,
                dia_semana=int(row.get("dia_semana", 6)),
                horario=time(int(hours), int(minutes)),
                observacao=row.get("observacao") or None,
            )
            db.add(schedule)
            created_schedules += 1
    db.commit()
    return {"created_churches": created_churches, "created_schedules": created_schedules}
