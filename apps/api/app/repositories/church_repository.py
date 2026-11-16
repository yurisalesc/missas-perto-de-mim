"""Church data access repository."""

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.church import Church
from app.models.confession_schedule import ConfessionSchedule
from app.models.mass_schedule import MassSchedule


class ChurchRepository:
    """Repository abstraction for church queries.

    Methods that mutate state flush but do not commit; callers own the unit of work.
    """

    def __init__(self, db: Session):
        """Create repository with database session."""

        self.db = db

    def list_with_schedules(self, city: str | None = None) -> list[Church]:
        """Return churches and their schedules, optionally filtered by city."""

        query = select(Church).options(joinedload(Church.mass_times))
        if city:
            city_value = city.strip()
            query = query.where(Church.cidade.ilike(f"%{city_value}%"))
        result = self.db.execute(query)
        return list(result.unique().scalars().all())

    def list_filtered(self, nome: str | None = None, cidade: str | None = None) -> list[Church]:
        """Return churches filtered by optional name/city icontains."""

        query = select(Church).order_by(Church.id.asc())
        if nome:
            query = query.where(Church.nome.ilike(f"%{nome.strip()}%"))
        if cidade:
            query = query.where(Church.cidade.ilike(f"%{cidade.strip()}%"))
        result = self.db.execute(query)
        return list(result.scalars().all())

    def list_filtered_page(
        self,
        *,
        nome: str | None = None,
        cidade: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Church], int]:
        """Return a page of churches filtered by optional name/city."""

        filters = []
        if nome:
            filters.append(Church.nome.ilike(f"%{nome.strip()}%"))
        if cidade:
            filters.append(Church.cidade.ilike(f"%{cidade.strip()}%"))

        count_query = select(func.count()).select_from(Church)
        list_query = select(Church).order_by(Church.id.asc())
        for condition in filters:
            count_query = count_query.where(condition)
            list_query = list_query.where(condition)

        total = int(self.db.execute(count_query).scalar_one())
        offset = max(page - 1, 0) * page_size
        items = list(self.db.execute(list_query.offset(offset).limit(page_size)).scalars().all())
        return items, total

    def list_cities(self, query_text: str | None = None, limit: int = 15) -> list[str]:
        """Return distinct cities for autocomplete, filtered by icontains."""

        query = select(distinct(Church.cidade)).order_by(Church.cidade.asc())
        if query_text:
            query = query.where(Church.cidade.ilike(f"%{query_text.strip()}%"))
        result = self.db.execute(query.limit(limit))
        return [row[0] for row in result.all() if row[0]]

    def list_cities_by_state(self) -> dict[str, list[str]]:
        """Return city names grouped by state and sorted alphabetically."""

        query = select(distinct(Church.estado), Church.cidade)
        result = self.db.execute(query).all()
        grouped: dict[str, set[str]] = {}
        for state, city in result:
            if not city:
                continue
            state_value = (state or "RN").strip().upper() or "RN"
            grouped.setdefault(state_value, set()).add(city.strip())
        return {state: sorted(values) for state, values in sorted(grouped.items(), key=lambda item: item[0])}

    def add(self, church: Church) -> Church:
        """Stage a new church (flush only; caller commits)."""

        self.db.add(church)
        self.db.flush()
        self.db.refresh(church)
        return church

    def get(self, church_id: int) -> Church | None:
        """Fetch church by id."""

        return self.db.get(Church, church_id)

    def get_with_schedules(self, church_id: int) -> Church | None:
        """Fetch church by id with mass and confession schedules loaded."""

        query = (
            select(Church)
            .where(Church.id == church_id)
            .options(joinedload(Church.mass_times), joinedload(Church.confession_times))
        )
        return self.db.execute(query).unique().scalar_one_or_none()

    def replace_mass_times(self, church: Church, schedules: list[MassSchedule]) -> None:
        """Replace all mass schedules for a church."""

        church.mass_times.clear()
        for schedule in schedules:
            church.mass_times.append(schedule)
        self.db.flush()

    def replace_confession_times(self, church: Church, schedules: list[ConfessionSchedule]) -> None:
        """Replace all confession schedules for a church."""

        church.confession_times.clear()
        for schedule in schedules:
            church.confession_times.append(schedule)
        self.db.flush()

    def delete(self, church: Church) -> None:
        """Stage deletion of a church (caller commits)."""

        self.db.delete(church)
        self.db.flush()
