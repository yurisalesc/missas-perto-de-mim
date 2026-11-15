"""Confession schedule schemas."""

from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfessionScheduleBase(BaseModel):
    """Shared confession range fields (read/write)."""

    dia_semana: int = Field(ge=0, le=6)
    horario_inicio: time
    horario_fim: time
    observacao: str | None = Field(default=None, max_length=255)


class ConfessionScheduleNested(ConfessionScheduleBase):
    """Nested confession range for church create/update payloads."""

    @model_validator(mode="after")
    def validate_range(self) -> "ConfessionScheduleNested":
        if self.horario_fim <= self.horario_inicio:
            raise ValueError("horario_fim must be after horario_inicio")
        return self


class ConfessionScheduleOut(ConfessionScheduleBase):
    """Response schema for a confession schedule.

    Intentionally does not enforce ``fim > início`` so legacy migrated rows
    (and any historically equal bounds) can still be serialized.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
