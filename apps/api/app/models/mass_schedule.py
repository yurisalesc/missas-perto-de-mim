"""Mass schedule ORM model."""

from datetime import time

from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MassSchedule(Base):
    """Represents a church mass schedule."""

    __tablename__ = "mass_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    church_id: Mapped[int] = mapped_column(ForeignKey("churches.id"), nullable=False, index=True)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    horario: Mapped[time] = mapped_column(Time, nullable=False, index=True)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    church = relationship("Church", back_populates="horarios")
