import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from api.core.config import settings
from api.database.base import Base
from api.database.session import get_db


@pytest.fixture(scope="session")
def engine():
    return create_engine(settings.database_url)


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Cria todas as tabelas antes do teste e derruba tudo depois.
    Usa o mesmo Postgres do CI (service container), não SQLite.
    """
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()