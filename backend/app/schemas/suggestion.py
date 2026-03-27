"""Suggestion schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SuggestionCreate(BaseModel):
    """Payload for a user suggestion."""

    nome_igreja: str = Field(min_length=2, max_length=255)
    endereco: str = Field(min_length=3, max_length=255)
    cidade: str = Field(min_length=2, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    mensagem: str | None = Field(default=None, max_length=2000)


class SuggestionOut(SuggestionCreate):
    """Response payload for a suggestion."""

    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SuggestionModeration(BaseModel):
    """Payload to moderate a suggestion."""

    status: str = Field(pattern="^(approved|rejected)$")
