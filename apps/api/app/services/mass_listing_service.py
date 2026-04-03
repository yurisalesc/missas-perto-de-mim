"""Application service for public mass listing endpoints."""

from app.core.text_normalization import normalize_search_token
from app.repositories.schedule_repository import ScheduleRepository
from app.schemas.mass_listing import MassListingOut


class MassListingService:
    """Encapsulates filtering/serialization rules for mass listings."""

    def __init__(self, schedule_repository: ScheduleRepository):
        self.schedule_repository = schedule_repository

    @staticmethod
    def _matches_turno(hour: int, turno: str | None) -> bool:
        if not turno:
            return True
        if turno == "manha":
            return hour < 12
        if turno == "tarde":
            return 12 <= hour < 18
        if turno == "noite":
            return hour >= 18
        return True

    @staticmethod
    def _to_item(schedule) -> MassListingOut:
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

    def list_week(self, dia_semana: int | None, turno: str | None) -> list[MassListingOut]:
        schedules = self.schedule_repository.list_all()
        items: list[MassListingOut] = []
        for schedule in schedules:
            if dia_semana is not None and schedule.dia_semana != dia_semana:
                continue
            if not self._matches_turno(schedule.horario.hour, turno):
                continue
            items.append(self._to_item(schedule))
        return items

    def list_all(
        self,
        cidade: str | None,
        nome_igreja: str | None,
        dia_semana: int | None,
        turno: str | None,
    ) -> list[MassListingOut]:
        schedules = self.schedule_repository.list_all()
        items: list[MassListingOut] = []
        city_filter = normalize_search_token(cidade) if cidade else None
        church_filter = normalize_search_token(nome_igreja) if nome_igreja else None

        for schedule in schedules:
            church_city = normalize_search_token(schedule.church.cidade)
            if city_filter and city_filter not in church_city:
                continue
            church_name = normalize_search_token(schedule.church.nome)
            if church_filter and church_filter not in church_name:
                continue
            if dia_semana is not None and schedule.dia_semana != dia_semana:
                continue
            if not self._matches_turno(schedule.horario.hour, turno):
                continue
            items.append(self._to_item(schedule))
        return items
