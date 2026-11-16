"""Church schemas."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.confession_schedule import ConfessionScheduleNested, ConfessionScheduleOut
from app.schemas.mass_schedule import MassScheduleNested, MassScheduleNestedOut

_UF_PATTERN = re.compile(r"^[A-Z]{2}$")


def normalize_estado(value: str | None) -> str | None:
    """Normalize and validate Brazilian UF codes."""

    if value is None:
        return None
    cleaned = value.strip().upper()
    if not cleaned:
        return None
    if not _UF_PATTERN.fullmatch(cleaned):
        raise ValueError("estado must be a 2-letter UF code")
    return cleaned


class ChurchBase(BaseModel):
    """Base payload for church data."""

    nome: str = Field(min_length=2, max_length=255)
    endereco: str = Field(min_length=3, max_length=255)
    cidade: str = Field(min_length=2, max_length=100)
    estado: str | None = Field(default=None, max_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    telefone: str | None = Field(default=None, max_length=60)
    redes_sociais_site: str | None = Field(default=None, max_length=255)
    observacao: str | None = Field(default=None, max_length=255)

    @field_validator("estado", mode="before")
    @classmethod
    def validate_estado(cls, value: object) -> str | None:
        if value is None or isinstance(value, str):
            return normalize_estado(value)
        raise ValueError("estado must be a string or null")


class ChurchCreate(ChurchBase):
    """Create payload for church."""

    mass_times: list[MassScheduleNested] | None = None
    confession_times: list[ConfessionScheduleNested] | None = None


class ChurchUpdate(BaseModel):
    """Update payload for church."""

    nome: str | None = Field(default=None, min_length=2, max_length=255)
    endereco: str | None = Field(default=None, min_length=3, max_length=255)
    cidade: str | None = Field(default=None, min_length=2, max_length=100)
    estado: str | None = Field(default=None, max_length=2)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    telefone: str | None = Field(default=None, max_length=60)
    redes_sociais_site: str | None = Field(default=None, max_length=255)
    observacao: str | None = Field(default=None, max_length=255)
    mass_times: list[MassScheduleNested] | None = None
    confession_times: list[ConfessionScheduleNested] | None = None

    @field_validator("estado", mode="before")
    @classmethod
    def validate_estado(cls, value: object) -> str | None:
        if value is None or isinstance(value, str):
            return normalize_estado(value)
        raise ValueError("estado must be a string or null")


class ChurchOut(ChurchBase):
    """Response schema for church list items."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class ChurchDetailOut(ChurchOut):
    """Response schema for church detail with schedules."""

    mass_times: list[MassScheduleNestedOut] = Field(default_factory=list)
    confession_times: list[ConfessionScheduleOut] = Field(default_factory=list)
