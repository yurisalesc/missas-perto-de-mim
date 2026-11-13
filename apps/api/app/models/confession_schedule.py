"""Confession schedule ORM model."""

from sqlalchemy.orm import relationship

from app.models.weekly_church_schedule import WeeklyChurchSchedule


class ConfessionSchedule(WeeklyChurchSchedule):
    """Represents a church confession schedule."""

    __tablename__ = "confession_schedules"

    church = relationship("Church", back_populates="confession_times")
