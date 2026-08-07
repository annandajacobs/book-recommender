import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database.base import Base

if TYPE_CHECKING:
    from api.models.user import User


class StatusLeitura(str, enum.Enum):
    LENDO = "lendo"
    CONCLUIDO = "concluido"
    ABANDONADO = "abandonado"


class FeedbackLeitura(str, enum.Enum):
    GOSTOU = "gostou"
    NAO_GOSTOU = "nao_gostou"
    NEUTRO = "neutro"


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    book_id: Mapped[str] = mapped_column(String(50))  
    titulo: Mapped[str] = mapped_column(String(500))
    autor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[StatusLeitura] = mapped_column(Enum(StatusLeitura, name="status_leitura_enum"), default=StatusLeitura.LENDO)
    feedback: Mapped[FeedbackLeitura | None] = mapped_column(Enum(FeedbackLeitura, name="feedback_leitura_enum"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="reading_history")