from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from api.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Função geradora que fornece uma sessão de banco de dados para cada requisição.
    Garante que a sessão seja fechada após o uso, evitando vazamentos de conexão.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()