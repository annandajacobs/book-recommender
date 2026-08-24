from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.user import User
from api.models.user_goal import UserGoal
from api.schemas.recommendation import RecommendationOut
from api.services.recommendation_service import NoBooksFoundError, RecommendationService

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/", response_model=RecommendationOut)
def get_recommendations(
    goal_id: int | None = Query(
        None, description="Se omitido, usa o objetivo ativo mais recente do usuário"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = _resolver_objetivo(goal_id, db, current_user)

    service = RecommendationService(db)
    try:
        return service.recommend(current_user, goal)
    except NoBooksFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


def _resolver_objetivo(goal_id: int | None, db: Session, current_user: User) -> UserGoal:
    query = db.query(UserGoal).filter(UserGoal.user_id == current_user.id)

    if goal_id is not None:
        goal = query.filter(UserGoal.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Objetivo não encontrado")
        return goal

    goal = (
        query.filter(UserGoal.ativo.is_(True)).order_by(UserGoal.created_at.desc()).first()
    )
    if not goal:
        raise HTTPException(
            status_code=400,
            detail="Você não tem nenhum objetivo ativo. Crie um em POST /api/v1/goals/ primeiro.",
        )
    return goal
