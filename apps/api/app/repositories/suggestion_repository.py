"""Suggestion repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.suggestion import UserSuggestion


class SuggestionRepository:
    """Repository abstraction for suggestion operations."""

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

    def get(self, suggestion_id: int) -> UserSuggestion | None:
        """Fetch suggestion by id."""

        return self.db.get(UserSuggestion, suggestion_id)
