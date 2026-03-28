"""Search orchestration service."""

from datetime import datetime, timedelta

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
        base_time = now + timedelta(hours=next_hours)
        window_hours = 2

        for church in churches:
            distance = None
            if lat is not None and lon is not None:
                distance = GeolocationService.haversine_distance(lat, lon, church.latitude, church.longitude)
                if distance > radius_km:
                    continue

            matches = MassTimeService.filter_in_window(base_time, list(church.horarios), window_hours)
            if not matches:
                continue

            nearest_match = matches[0]
            schedule, occurrence = nearest_match
            response_masses = [
                SearchResultMass(
                    mass_schedule_id=schedule.id,
                    dia_semana=schedule.dia_semana,
                    horario=schedule.horario,
                    ocorrencia_em=occurrence,
                    observacao=schedule.observacao,
                )
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
                    telefone=church.telefone,
                    redes_sociais_site=church.redes_sociais_site,
                    observacao=church.observacao,
                    proximas_missas=response_masses,
                )
            )

        results.sort(key=lambda item: item.distancia_km)
        return results

    def search_happening_now(self, now: datetime, city: str | None) -> list[SearchResultChurch]:
        """Search churches where at least one mass is happening now."""

        churches = self.church_repository.list_with_schedules(city=city)
        results: list[SearchResultChurch] = []

        for church in churches:
            matches = MassTimeService.filter_happening_now(now, list(church.horarios), duration_minutes=90)
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
                    distancia_km=0.0,
                    telefone=church.telefone,
                    redes_sociais_site=church.redes_sociais_site,
                    observacao=church.observacao,
                    proximas_missas=response_masses,
                )
            )

        results.sort(key=lambda item: item.nome.lower())
        return results
