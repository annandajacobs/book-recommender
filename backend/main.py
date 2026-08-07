from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.v1.auth import router as auth_router
from api.v1.goals import router as goals_router
from api.v1.preferences import router as preferences_router
from api.v1.reading_history import router as reading_history_router

app = FastAPI(
    title="Book Recommender API",
    description="API para recomendação de livros baseada em preferências do usuário.",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(preferences_router)
app.include_router(goals_router)
app.include_router(reading_history_router)

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "Book Recommender API"
    }

@app.get("/health/db")
def health_check_db(db: Session =Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected"
        }
    except SQLAlchemyError as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }