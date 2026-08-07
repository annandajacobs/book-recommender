from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PreferenceCreate(BaseModel):
    genero: str
    peso: float = Field(default=0.5, ge=0.0, le=1.0)


class PreferenceUpdate(BaseModel):
    peso: float = Field(ge=0.0, le=1.0)


class PreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    genero: str
    peso: float
    updated_at: datetime