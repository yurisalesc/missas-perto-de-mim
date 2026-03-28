"""Weekly mass exploration endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.text_normalization import normalize_search_token
from app.db.session import get_db
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.mass_listing import MassListingOut

router = APIRouter(prefix="/missas", tags=["missas"])


def matches_turno(hour: int, turno: str | None) -> bool:
    """Return true when hour belongs to the requested shift."""

    if not turno:
        return True
    if turno == "manha":
        return hour < 12
    if turno == "tarde":
        return 12 <= hour < 18
    if turno == "noite":
        return hour >= 18
    return True


def schedule_to_item(schedule) -> MassListingOut:
    """Serialize schedule row into stable API contract."""

    return MassListingOut(
        schedule_id=schedule.id,
        church_id=schedule.church.id,
        nome_igreja=schedule.church.nome,
        cidade=schedule.church.cidade,
        dia_semana=schedule.dia_semana,
        horario=schedule.horario.isoformat(timespec="minutes"),
        observacao=schedule.observacao,
        telefone=schedule.church.telefone,
        redes_sociais_site=schedule.church.redes_sociais_site,
    )


@router.get("/semana", response_model=list[MassListingOut])
def list_week_masses(
    dia_semana: int | None = None,
    turno: str | None = None,
    db: Session = Depends(get_db),
) -> list[MassListingOut]:
    """List weekly masses with optional day and shift filters."""

    schedules = ScheduleRepository(db).list_all()
    items: list[MassListingOut] = []
    for schedule in schedules:
        if dia_semana is not None and schedule.dia_semana != dia_semana:
            continue
        if not matches_turno(schedule.horario.hour, turno):
                continue
        items.append(schedule_to_item(schedule))
    return items


@router.get("/todas", response_model=list[MassListingOut])
def list_all_masses(
    cidade: str | None = None,
    nome_igreja: str | None = None,
    dia_semana: int | None = None,
    turno: str | None = None,
    db: Session = Depends(get_db),
) -> list[MassListingOut]:
    """List all masses and allow filtering by church name."""

    schedules = ScheduleRepository(db).list_all()
    items: list[MassListingOut] = []
    city_filter = normalize_search_token(cidade) if cidade else None
    filter_value = normalize_search_token(nome_igreja) if nome_igreja else None
    for schedule in schedules:
        church_city = normalize_search_token(schedule.church.cidade)
        if city_filter and city_filter not in church_city:
            continue
        church_name = normalize_search_token(schedule.church.nome)
        if filter_value and filter_value not in church_name:
            continue
        if dia_semana is not None and schedule.dia_semana != dia_semana:
            continue
        if not matches_turno(schedule.horario.hour, turno):
                continue
        items.append(schedule_to_item(schedule))
    return items
