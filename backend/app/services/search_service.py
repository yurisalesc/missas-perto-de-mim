"""Search orchestration service."""

from datetime import datetime

from app.repositories.church_repository import ChurchRepository
from app.schemas.search import SearchResultChurch, SearchResultMass
from app.services.geolocation_service import GeolocationService
from app.services.mass_time_service import MassTimeService


class SearchService:
    """Application service for church and mass search use cases."""

    def __init__(self, church_repository: ChurchRepository):
        """Create service with repository dependency."""

        self.church_repository = church_repository

    def search(
        self,
        now: datetime,
        lat: float | None,
        lon: float | None,
        radius_km: int,
        city: str | None,
        next_hours: int,
    ) -> list[SearchResultChurch]:
        """Search churches and masses by city, distance and time window."""

        churches = self.church_repository.list_with_schedules(city=city)
        results: list[SearchResultChurch] = []

        for church in churches:
            distance = None
            if lat is not None and lon is not None:
                distance = GeolocationService.haversine_distance(lat, lon, church.latitude, church.longitude)
                if distance > radius_km:
                    continue

            matches = MassTimeService.filter_in_window(now, list(church.horarios), next_hours)
            if not matches:
                continue

            response_masses = [
                SearchResultMass(
                    mass_schedule_id=schedule.id,
                    dia_semana=schedule.dia_semana,
                    horario=schedule.horario,
                    ocorrencia_em=occurrence,
                    observacao=schedule.observacao,
                )
                for schedule, occurrence in matches
            ]
            results.append(
                SearchResultChurch(
                    church_id=church.id,
                    nome=church.nome,
                    endereco=church.endereco,
                    cidade=church.cidade,
                    latitude=church.latitude,
                    longitude=church.longitude,
                    distancia_km=round(distance if distance is not None else 0.0, 3),
                    proximas_missas=response_masses,
                )
            )

        results.sort(key=lambda item: item.distancia_km)
        return results
