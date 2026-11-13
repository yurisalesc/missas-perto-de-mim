"""Mass schedule ORM model."""

from sqlalchemy.orm import relationship

from app.models.weekly_church_schedule import WeeklyChurchSchedule


class MassSchedule(WeeklyChurchSchedule):
    """Represents a church mass schedule."""

    __tablename__ = "mass_schedules"

    church = relationship("Church", back_populates="mass_times")
