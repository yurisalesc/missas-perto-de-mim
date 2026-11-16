"""Application service for admin church CRUD with nested schedules."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.text_normalization import expand_nossa_senhora
from app.models.church import Church
from app.models.confession_schedule import ConfessionSchedule
from app.models.mass_schedule import MassSchedule
from app.repositories.church_repository import ChurchRepository
from app.schemas.church import ChurchCreate, ChurchUpdate
from app.schemas.confession_schedule import ConfessionScheduleNested
from app.schemas.mass_schedule import MassScheduleNested
from app.schemas.pagination import Page

CHURCH_FIELD_KEYS = {
    "nome",
    "endereco",
    "cidade",
    "estado",
    "latitude",
    "longitude",
    "telefone",
    "redes_sociais_site",
    "observacao",
}


class ChurchAdminService:
    """Orchestrates church persistence and nested schedule replace semantics."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ChurchRepository(db)

    @staticmethod
    def _build_mass_schedules(items: list[MassScheduleNested] | None) -> list[MassSchedule]:
        if not items:
            return []
        return [
            MassSchedule(
                dia_semana=item.dia_semana,
                horario=item.horario,
                observacao=item.observacao,
            )
            for item in items
        ]

    @staticmethod
    def _build_confession_schedules(
        items: list[ConfessionScheduleNested] | None,
    ) -> list[ConfessionSchedule]:
        if not items:
            return []
        return [
            ConfessionSchedule(
                dia_semana=item.dia_semana,
                horario_inicio=item.horario_inicio,
                horario_fim=item.horario_fim,
                observacao=item.observacao,
            )
            for item in items
        ]

    def create(self, payload: ChurchCreate) -> Church:
        data = payload.model_dump(exclude={"mass_times", "confession_times"})
        data["nome"] = expand_nossa_senhora(data["nome"])
        data["estado"] = data.get("estado") or "RN"
        church = Church(**data)
        for schedule in self._build_mass_schedules(payload.mass_times):
            church.mass_times.append(schedule)
        for schedule in self._build_confession_schedules(payload.confession_times):
            church.confession_times.append(schedule)

        try:
            church = self.repo.add(church)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        detail = self.repo.get_with_schedules(church.id)
        if detail is None:
            raise HTTPException(status_code=500, detail="Church was created but could not be reloaded")
        return detail

    def get(self, church_id: int) -> Church:
        church = self.repo.get_with_schedules(church_id)
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        return church

    def list_page(
        self,
        *,
        nome: str | None = None,
        cidade: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> Page[Church]:
        items, total = self.repo.list_filtered_page(
            nome=nome,
            cidade=cidade,
            page=page,
            page_size=page_size,
        )
        return Page(items=items, total=total, page=page, page_size=page_size)

    def list_all_filtered(self, *, nome: str | None = None, cidade: str | None = None) -> list[Church]:
        return self.repo.list_filtered(nome=nome, cidade=cidade)

    def update(self, church_id: int, payload: ChurchUpdate) -> Church:
        church = self.repo.get_with_schedules(church_id)
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        data = payload.model_dump(exclude_unset=True)
        mass_times = data.pop("mass_times", None)
        confession_times = data.pop("confession_times", None)

        if "nome" in data and data["nome"] is not None:
            data["nome"] = expand_nossa_senhora(data["nome"])

        try:
            for key, value in data.items():
                if key in CHURCH_FIELD_KEYS:
                    setattr(church, key, value)

            if mass_times is not None:
                self.repo.replace_mass_times(church, self._build_mass_schedules(payload.mass_times))
            if confession_times is not None:
                self.repo.replace_confession_times(
                    church, self._build_confession_schedules(payload.confession_times)
                )

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        detail = self.repo.get_with_schedules(church_id)
        if detail is None:
            raise HTTPException(status_code=500, detail="Church was updated but could not be reloaded")
        return detail

    def delete(self, church_id: int) -> None:
        church = self.repo.get(church_id)
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        try:
            self.repo.delete(church)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
