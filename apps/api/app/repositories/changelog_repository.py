"""Changelog repository."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.changelog import ChangelogEntry

_FORTALEZA_TZ = ZoneInfo("America/Fortaleza")


class ChangelogRepository:
    """Repository abstraction for changelog operations."""

    def __init__(self, db: Session):
        """Create repository with database session."""

        self.db = db

    def list_last_days(self, days: int) -> list[ChangelogEntry]:
        """Return entries published in the last N days."""

        cutoff = datetime.now(_FORTALEZA_TZ).replace(tzinfo=None) - timedelta(days=days)
        query = (
            select(ChangelogEntry)
            .where(ChangelogEntry.published_at >= cutoff)
            .order_by(ChangelogEntry.published_at.desc(), ChangelogEntry.id.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def list_all(self) -> list[ChangelogEntry]:
        """Return all entries sorted by most recent."""

        query = select(ChangelogEntry).order_by(ChangelogEntry.published_at.desc(), ChangelogEntry.id.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    def create(self, entry: ChangelogEntry) -> ChangelogEntry:
        """Persist a new changelog entry."""

        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get(self, entry_id: int) -> ChangelogEntry | None:
        """Fetch changelog entry by id."""

        return self.db.get(ChangelogEntry, entry_id)

    def update(self, entry: ChangelogEntry) -> ChangelogEntry:
        """Persist updates for an existing changelog entry."""

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry: ChangelogEntry) -> None:
        """Delete an existing changelog entry."""

        self.db.delete(entry)
        self.db.commit()
