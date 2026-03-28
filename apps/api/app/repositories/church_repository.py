"""Church data access repository."""

from sqlalchemy import distinct, select
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

    def list_filtered(self, nome: str | None = None, cidade: str | None = None) -> list[Church]:
        """Return churches filtered by optional name/city icontains."""

        query = select(Church).options(joinedload(Church.horarios))
        if nome:
            query = query.where(Church.nome.ilike(f"%{nome.strip()}%"))
        if cidade:
            query = query.where(Church.cidade.ilike(f"%{cidade.strip()}%"))
        result = self.db.execute(query)
        return list(result.unique().scalars().all())

    def list_cities(self, query_text: str | None = None, limit: int = 15) -> list[str]:
        """Return distinct cities for autocomplete, filtered by icontains."""

        query = select(distinct(Church.cidade)).order_by(Church.cidade.asc())
        if query_text:
            query = query.where(Church.cidade.ilike(f"%{query_text.strip()}%"))
        result = self.db.execute(query.limit(limit))
        return [row[0] for row in result.all() if row[0]]

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
