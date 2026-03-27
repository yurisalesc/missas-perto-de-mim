"""Mass schedule schemas."""

from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class MassScheduleBase(BaseModel):
    """Base payload for mass schedule."""

    church_id: int
    dia_semana: int = Field(ge=0, le=6)
    horario: time
    observacao: str | None = Field(default=None, max_length=255)


class MassScheduleCreate(MassScheduleBase):
    """Create payload for mass schedule."""


class MassScheduleUpdate(BaseModel):
    """Update payload for mass schedule."""

    church_id: int | None = None
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    horario: time | None = None
    observacao: str | None = Field(default=None, max_length=255)


class MassScheduleOut(MassScheduleBase):
    """Response schema for mass schedule."""

    id: int

    model_config = ConfigDict(from_attributes=True)
