"""Weekly mass exploration endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.mass_listing import MassListingOut
from app.services.mass_listing_service import MassListingService

router = APIRouter(prefix="/missas", tags=["missas"])


@router.get("/semana", response_model=list[MassListingOut])
def list_week_masses(
    dia_semana: int | None = None,
    turno: str | None = None,
    db: Session = Depends(get_db),
) -> list[MassListingOut]:
    """List weekly masses with optional day and shift filters."""

    service = MassListingService(ScheduleRepository(db))
    return service.list_week(dia_semana=dia_semana, turno=turno)


@router.get("/todas", response_model=list[MassListingOut])
def list_all_masses(
    cidade: str | None = None,
    nome_igreja: str | None = None,
    dia_semana: int | None = None,
    turno: str | None = None,
    db: Session = Depends(get_db),
) -> list[MassListingOut]:
    """List all masses and allow filtering by church name."""

    service = MassListingService(ScheduleRepository(db))
    return service.list_all(
        cidade=cidade,
        nome_igreja=nome_igreja,
        dia_semana=dia_semana,
        turno=turno,
    )
