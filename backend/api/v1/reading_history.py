from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.reading_history import ReadingHistory, StatusLeitura
from api.models.user import User
from api.schemas.reading_history import (
    ReadingHistoryCreate,
    ReadingHistoryOut,
    ReadingHistoryUpdate,
)

router = APIRouter(prefix="/api/v1/reading-history", tags=["reading-history"])

@router.post("/", response_model=ReadingHistoryOut, status_code=status.HTTP_201_CREATED)
def create_reading_entry(
    payload: ReadingHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = ReadingHistory(user_id = current_user.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[ReadingHistoryOut])
def list_reading_history(
    status_filtro: StatusLeitura | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id)
    if status_filtro:
        query = query.filter(ReadingHistory.status == status_filtro)
    return query.all()


def _get_owned_entry(entry_id: int, db: Session, current_user: User) -> ReadingHistory:
    entry = (
        db.query(ReadingHistory)
        .filter(ReadingHistory.id == entry_id, ReadingHistory.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Registro de leitura não encontrado")
    return entry


@router.patch("/{entry_id}", response_model=ReadingHistoryOut)
def update_reading_entry(
    entry_id: int,
    payload: ReadingHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_owned_entry(entry_id, db, current_user)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(entry, field, value)

    if updates.get("status") == StatusLeitura.CONCLUIDO and entry.finished_at is None:
        entry.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reading_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_owned_entry(entry_id, db, current_user)
    db.delete(entry)
    db.commit()
