from datetime import datetime
from pydantic import BaseModel, ConfigDict
from api.models.user_goal import NivelConhecimento


class GoalCreate(BaseModel):
    objetivo: str
    nivel_conhecimento: NivelConhecimento = NivelConhecimento.INICIANTE


class GoalUpdate(BaseModel):
    nivel_conhecimento: NivelConhecimento | None = None
    ativo: bool | None = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    objetivo: str
    nivel_conhecimento: NivelConhecimento
    ativo: bool
    created_at: datetime