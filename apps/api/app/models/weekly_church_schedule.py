"""Shared abstract base for weekly church schedule tables."""

from datetime import time

from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeeklyChurchSchedule(Base):
    """Abstract weekly schedule shared by mass and confession tables.

    Concrete subclasses must define their own ``__tablename__`` and the
    bidirectional ``church`` relationship with a distinct ``back_populates``
    name to keep ORM associations unambiguous.
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    church_id: Mapped[int] = mapped_column(ForeignKey("churches.id"), nullable=False, index=True)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    horario: Mapped[time] = mapped_column(Time, nullable=False, index=True)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
