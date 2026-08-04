from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session
from api.database.session import get_db
from api.v1.auth import router as auth_router

app = FastAPI(
    title="Book Recommender API",
    description="API para recomendação de livros baseada em preferências do usuário.",
    version="0.1.0",
)

app.include_router(auth_router)

@app.get("/")
def health_check():
    """
    Endpoint de verificação de saúde da API.
    Retorna uma mensagem simples indicando que a API está funcionando corretamente.
    """
    return {"message": "ok", "service": "Book Recommender API"}

@app.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """
    Endpoint de verificação de saúde do banco de dados.
    Tenta executar uma consulta simples para garantir que a conexão com o banco de dados está funcionando.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"message": "ok"}
    except Exception as e:
        return {"message": "Database connection failed.", "error": str(e)}