"""Changelog schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.changelog import ChangelogBadge


class ChangelogBase(BaseModel):
    """Base payload for changelog entries."""

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=3, max_length=2000)
    badge: ChangelogBadge
    published_at: datetime | None = None


class ChangelogCreate(ChangelogBase):
    """Create payload for changelog entry."""


class ChangelogUpdate(BaseModel):
    """Update payload for changelog entry."""

    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, min_length=3, max_length=2000)
    badge: ChangelogBadge | None = None
    published_at: datetime | None = None


class ChangelogOut(BaseModel):
    """Response payload for changelog entry."""

    id: int
    title: str
    description: str
    badge: ChangelogBadge
    published_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
