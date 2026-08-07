from datetime import datetime

from pydantic import BaseModel, ConfigDict

from api.models.reading_history import FeedbackLeitura, StatusLeitura


class ReadingHistoryCreate(BaseModel):
    book_id: str
    titulo: str
    autor: str | None = None
    status: StatusLeitura = StatusLeitura.LENDO


class ReadingHistoryUpdate(BaseModel):
    status: StatusLeitura | None = None
    feedback: FeedbackLeitura | None = None


class ReadingHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: str
    titulo: str
    autor: str | None
    status: StatusLeitura
    feedback: FeedbackLeitura | None
    started_at: datetime
    finished_at: datetime | None