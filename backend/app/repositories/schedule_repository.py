"""Mass schedule repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.mass_schedule import MassSchedule


class ScheduleRepository:
    """Repository abstraction for schedules."""

    def __init__(self, db: Session):
        """Create repository with database session."""

        self.db = db

    def list_all(self) -> list[MassSchedule]:
        """List schedules including church relationship."""

        query = select(MassSchedule).options(joinedload(MassSchedule.church))
        result = self.db.execute(query)
        return list(result.scalars().all())

    def create(self, schedule: MassSchedule) -> MassSchedule:
        """Persist a new schedule."""

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def get(self, schedule_id: int) -> MassSchedule | None:
        """Fetch schedule by id."""

        return self.db.get(MassSchedule, schedule_id)

    def delete(self, schedule: MassSchedule) -> None:
        """Delete an existing schedule."""

        self.db.delete(schedule)
        self.db.commit()
