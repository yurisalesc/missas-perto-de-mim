"""Church data access repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.church import Church


class ChurchRepository:
    """Repository abstraction for church queries."""

    def __init__(self, db: Session):
        """Create repository with database session."""

        self.db = db

    def list_with_schedules(self, city: str | None = None) -> list[Church]:
        """Return churches and their schedules, optionally filtered by city."""

        query = select(Church).options(joinedload(Church.horarios))
        if city:
            city_value = city.strip()
            query = query.where(Church.cidade.ilike(f"%{city_value}%"))
        result = self.db.execute(query)
        return list(result.unique().scalars().all())

    def create(self, church: Church) -> Church:
        """Persist a new church."""

        self.db.add(church)
        self.db.commit()
        self.db.refresh(church)
        return church

    def get(self, church_id: int) -> Church | None:
        """Fetch church by id."""

        return self.db.get(Church, church_id)

    def delete(self, church: Church) -> None:
        """Delete an existing church."""

        self.db.delete(church)
        self.db.commit()
