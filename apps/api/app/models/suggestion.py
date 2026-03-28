"""User suggestion ORM model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserSuggestion(Base):
    """Represents a pending or moderated user suggestion."""

    __tablename__ = "user_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome_igreja: Mapped[str] = mapped_column(String(255), nullable=False)
    endereco: Mapped[str] = mapped_column(String(255), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
