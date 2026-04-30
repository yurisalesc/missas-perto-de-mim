"""Changelog ORM model."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ChangelogBadge(str, Enum):
    """Badge types displayed in frontend entries."""

    NEW = "new"
    IMPROVED = "improved"
    FIXED = "fixed"


class ChangelogEntry(Base):
    """Represents a published changelog item."""

    __tablename__ = "changelog_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    badge: Mapped[ChangelogBadge] = mapped_column(
        SqlEnum(
            ChangelogBadge,
            name="changelog_badge_enum",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            validate_strings=True,
        ),
        nullable=False,
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
