"""Schemas for mass listing endpoints."""

from pydantic import BaseModel, ConfigDict


class MassListingOut(BaseModel):
    """Mass list item exposed by public listing endpoints."""

    schedule_id: int
    church_id: int
    nome_igreja: str
    cidade: str
    dia_semana: int
    horario: str
    observacao: str | None

    model_config = ConfigDict(from_attributes=True)

