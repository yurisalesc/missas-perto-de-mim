"""Church schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ChurchBase(BaseModel):
    """Base payload for church data."""

    nome: str = Field(min_length=2, max_length=255)
    endereco: str = Field(min_length=3, max_length=255)
    cidade: str = Field(min_length=2, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    telefone: str | None = Field(default=None, max_length=60)
    redes_sociais_site: str | None = Field(default=None, max_length=255)
    observacao: str | None = Field(default=None, max_length=255)


class ChurchCreate(ChurchBase):
    """Create payload for church."""


class ChurchUpdate(BaseModel):
    """Update payload for church."""

    nome: str | None = Field(default=None, min_length=2, max_length=255)
    endereco: str | None = Field(default=None, min_length=3, max_length=255)
    cidade: str | None = Field(default=None, min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    telefone: str | None = Field(default=None, max_length=60)
    redes_sociais_site: str | None = Field(default=None, max_length=255)
    observacao: str | None = Field(default=None, max_length=255)


class ChurchOut(ChurchBase):
    """Response schema for church."""

    id: int

    model_config = ConfigDict(from_attributes=True)
