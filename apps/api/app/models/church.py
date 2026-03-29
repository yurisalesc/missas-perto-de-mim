"""Church ORM model."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Church(Base):
    """Represents a church with geolocation data."""

    __tablename__ = "churches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    endereco: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    estado: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    redes_sociais_site: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    horarios = relationship("MassSchedule", back_populates="church", cascade="all, delete-orphan")
