"""Suggestion repository."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.suggestion import UserSuggestion


class SuggestionRepository:
    """Repository abstraction for suggestion operations.

    Mutating helpers flush only; callers own the unit of work.
    """

    def __init__(self, db: Session):
        """Create repository with database session."""

        self.db = db

    def create(self, suggestion: UserSuggestion) -> UserSuggestion:
        """Persist a new suggestion."""

        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def list_all(self) -> list[UserSuggestion]:
        """Return all suggestions sorted by most recent."""

        query = select(UserSuggestion).order_by(UserSuggestion.created_at.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    def list_page(self, *, page: int = 1, page_size: int = 25) -> tuple[list[UserSuggestion], int]:
        """Return a page of suggestions sorted by most recent."""

        total = int(self.db.execute(select(func.count()).select_from(UserSuggestion)).scalar_one())
        offset = max(page - 1, 0) * page_size
        query = (
            select(UserSuggestion)
            .order_by(UserSuggestion.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(self.db.execute(query).scalars().all())
        return items, total

    def get(self, suggestion_id: int) -> UserSuggestion | None:
        """Fetch suggestion by id."""

        return self.db.get(UserSuggestion, suggestion_id)

    def save(self, suggestion: UserSuggestion) -> UserSuggestion:
        """Flush updates for an existing suggestion (caller commits)."""

        self.db.add(suggestion)
        self.db.flush()
        self.db.refresh(suggestion)
        return suggestion
