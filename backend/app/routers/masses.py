"""Weekly mass exploration endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.schedule_repository import ScheduleRepository

router = APIRouter(prefix="/missas", tags=["missas"])


@router.get("/semana")
def list_week_masses(
    dia_semana: int | None = None,
    turno: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List weekly masses with optional day and shift filters."""

    schedules = ScheduleRepository(db).list_all()
    items: list[dict] = []
    for schedule in schedules:
        if dia_semana is not None and schedule.dia_semana != dia_semana:
            continue
        if turno:
            hour = schedule.horario.hour
            if turno == "manha" and hour >= 12:
                continue
            if turno == "tarde" and (hour < 12 or hour >= 18):
                continue
            if turno == "noite" and hour < 18:
                continue
        items.append(
            {
                "schedule_id": schedule.id,
                "church_id": schedule.church.id,
                "nome_igreja": schedule.church.nome,
                "cidade": schedule.church.cidade,
                "dia_semana": schedule.dia_semana,
                "horario": schedule.horario.isoformat(timespec="minutes"),
                "observacao": schedule.observacao,
            }
        )
    return items


@router.get("/todas")
def list_all_masses(
    nome_igreja: str | None = None,
    dia_semana: int | None = None,
    turno: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List all masses and allow filtering by church name."""

    schedules = ScheduleRepository(db).list_all()
    items: list[dict] = []
    for schedule in schedules:
        if nome_igreja and nome_igreja.strip().lower() not in schedule.church.nome.lower():
            continue
        if dia_semana is not None and schedule.dia_semana != dia_semana:
            continue
        if turno:
            hour = schedule.horario.hour
            if turno == "manha" and hour >= 12:
                continue
            if turno == "tarde" and (hour < 12 or hour >= 18):
                continue
            if turno == "noite" and hour < 18:
                continue
        items.append(
            {
                "schedule_id": schedule.id,
                "church_id": schedule.church.id,
                "nome_igreja": schedule.church.nome,
                "cidade": schedule.church.cidade,
                "dia_semana": schedule.dia_semana,
                "horario": schedule.horario.isoformat(timespec="minutes"),
                "observacao": schedule.observacao,
            }
        )
    return items
