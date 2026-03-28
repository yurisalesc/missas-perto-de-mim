"""Admin endpoints for schedule CRUD."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import get_db
from app.models.mass_schedule import MassSchedule
from app.repositories.church_repository import ChurchRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.mass_schedule import MassScheduleCreate, MassScheduleOut, MassScheduleUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/horarios", response_model=MassScheduleOut, status_code=201)
def create_schedule(payload: MassScheduleCreate, db: Session = Depends(get_db)) -> MassSchedule:
    church = ChurchRepository(db).get(payload.church_id)
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return ScheduleRepository(db).create(MassSchedule(**payload.model_dump()))


@router.get("/horarios", response_model=list[MassScheduleOut])
def list_schedules(db: Session = Depends(get_db)) -> list[MassSchedule]:
    return ScheduleRepository(db).list_all()


@router.patch("/horarios/{schedule_id}", response_model=MassScheduleOut)
def update_schedule(
    schedule_id: int, payload: MassScheduleUpdate, db: Session = Depends(get_db)
) -> MassSchedule:
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
    schedule = ScheduleRepository(db).get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    ScheduleRepository(db).delete(schedule)

