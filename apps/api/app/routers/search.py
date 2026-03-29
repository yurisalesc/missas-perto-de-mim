"""Search endpoints."""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.church_repository import ChurchRepository
from app.schemas.search import SearchQuery, SearchResultChurch
from app.services.search_service import SearchService

router = APIRouter(prefix="/igrejas", tags=["busca"])
RN_TZ = ZoneInfo("America/Fortaleza")


@router.get("/buscar", response_model=list[SearchResultChurch])
def search_churches(
    lat: float | None = None,
    lon: float | None = None,
    radius_km: int = 10,
    city: str | None = None,
    next_hours: int = 6,
    db: Session = Depends(get_db),
) -> list[SearchResultChurch]:
    """Search masses by optional location and city filters."""

    query = SearchQuery(lat=lat, lon=lon, radius_km=radius_km, city=city, next_hours=next_hours)
    if (query.lat is None) != (query.lon is None):
        raise HTTPException(status_code=422, detail="lat and lon must be provided together")
    service = SearchService(ChurchRepository(db))
    return service.search(
        now=datetime.now(RN_TZ).replace(tzinfo=None),
        lat=query.lat,
        lon=query.lon,
        radius_km=query.radius_km,
        city=query.city,
        next_hours=query.next_hours,
    )


@router.get("/cidades", response_model=list[str])
def suggest_cities(
    q: str | None = None,
    limit: int = 15,
    db: Session = Depends(get_db),
) -> list[str]:
    """Autocomplete cities from existing churches."""

    return ChurchRepository(db).list_cities(query_text=q, limit=max(1, min(limit, 50)))


@router.get("/cidades-por-estado", response_model=dict[str, list[str]])
def list_cities_by_state(db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return available cities grouped by state."""

    return ChurchRepository(db).list_cities_by_state()


@router.get("/acontecendo-agora", response_model=list[SearchResultChurch])
def happening_now(
    city: str | None = None,
    db: Session = Depends(get_db),
) -> list[SearchResultChurch]:
    """List churches with masses happening now (duration assumed 1h30)."""

    service = SearchService(ChurchRepository(db))
    return service.search_happening_now(
        now=datetime.now(RN_TZ).replace(tzinfo=None),
        city=city.strip() if city else None,
    )
