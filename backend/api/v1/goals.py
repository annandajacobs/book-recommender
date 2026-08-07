from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.user import User
from api.models.user_goal import UserGoal
from api.schemas.user_goal import GoalCreate, GoalOut, GoalUpdate

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])

@router.post("/", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = UserGoal(user_id=current_user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/", response_model=list[GoalOut])
def list_goal(
    apenas_ativos: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(UserGoal).filter(UserGoal.user_id == current_user.id)
    if apenas_ativos:
        query = query.filter(UserGoal.ativo.is_(True))
    return query.all()


def _get_owned_goal(goal_id: int, db: Session, current_user: User) -> UserGoal:
    goal = (
        db.query(UserGoal)
        .filter(UserGoal.id == goal_id, UserGoal.user_id == current_user.id)
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Objetivo não encontado.")
    return goal

@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = _get