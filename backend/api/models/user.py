from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database.base import Base

if TYPE_CHECKING:
    from api.models.reading_history import ReadingHistory
    from api.models.user_goal import UserGoal
    from api.models.user_preference import UserPreference


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))

    idioma_preferido: Mapped[str] = mapped_column(String(10), default="pt")
    tempo_disponivel_semanal: Mapped[int | None] = mapped_column(default=None)  # em minutos

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    preferences: Mapped[list["UserPreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["UserGoal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reading_history: Mapped[list["ReadingHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
