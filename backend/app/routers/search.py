"""Search endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.church_repository import ChurchRepository
from app.schemas.search import SearchQuery, SearchResultChurch
from app.services.search_service import SearchService

router = APIRouter(prefix="/igrejas", tags=["busca"])


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
        now=datetime.now(timezone.utc).replace(tzinfo=None),
        lat=query.lat,
        lon=query.lon,
        radius_km=query.radius_km,
        city=query.city,
        next_hours=query.next_hours,
    )
