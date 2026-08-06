from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    idioma_preferido: str = "pt"


class UserLogin(BaseModel):
    email: EmailStr
    senha: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    idioma_preferido: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

