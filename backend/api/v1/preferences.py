from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.user import User
from api.models.user_preference import UserPreference
from api.schemas.user_preference import (
    PreferenceCreate,
    PreferenceOut,
    PreferenceUpdate,
)

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


@router.post("/", response_model=PreferenceOut, status_code=status.HTTP_201_CREATED)
def create_preference(
    payload: PreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(UserPreference)
        .filter(
            UserPreference.user_id == current_user.id,
            UserPreference.genero == payload.genero,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Gênero já cadastrado para este usuário")

    preference = UserPreference(user_id=current_user.id, **payload.model_dump())
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


@router.get("/", response_model=list[PreferenceOut])
def list_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(UserPreference).filter(UserPreference.user_id == current_user.id).all()
    )


def _get_owned_preference(
    preference_id: int, db: Session, current_user: User
) -> UserPreference:
    preference = (
        db.query(UserPreference)
        .filter(
            UserPreference.id == preference_id,
            UserPreference.user_id == current_user.id,
        )
        .first()
    )
    if not preference:
        raise HTTPException(status_code=404, detail="Preferência não encontrada")
    return preference


@router.patch("/{preference_id}", response_model=PreferenceOut)
def update_preference(
    preference_id: int,
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preference = _get_owned_preference(preference_id, db, current_user)
    preference.peso = payload.peso
    db.commit()
    db.refresh(preference)
    return preference


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preference(
    preference_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preference = _get_owned_preference(preference_id, db, current_user)
    db.delete(preference)
    db.commit()
