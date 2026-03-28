"""Search schemas."""

from datetime import datetime, time

from pydantic import BaseModel, Field


class SearchResultMass(BaseModel):
    """Mass info returned in search results."""

    mass_schedule_id: int
    dia_semana: int
    horario: time
    ocorrencia_em: datetime
    observacao: str | None


class SearchResultChurch(BaseModel):
    """Church result with distance and matching masses."""

    church_id: int
    nome: str
    endereco: str
    cidade: str
    latitude: float
    longitude: float
    distancia_km: float
    telefone: str | None = None
    redes_sociais_site: str | None = None
    observacao: str | None = None
    proximas_missas: list[SearchResultMass]


class SearchQuery(BaseModel):
    """Allowed query params for dynamic search."""

    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    radius_km: int = Field(default=10, ge=1, le=50)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    next_hours: int = Field(default=6, ge=1, le=168)
