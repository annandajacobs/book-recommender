from fastapi import APIRouter, Depends, Query

from api.core.deps import get_current_user
from api.infrastructure.google_books.client import GoogleBooksClient
from api.infrastructure.google_books.query_builder import build_query_from_goal
from api.infrastructure.google_books.schemas import BookCandidate
from api.models.user import User

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("/search", response_model=list[BookCandidate])
def search_books(
    objetivo: str = Query(..., description="Ex: 'aprender python', 'filosofia'"),
    idioma: str | None = Query(None, description="ISO 639-1, ex: 'pt', 'en'"),
    max_results: int = Query(10, ge=1, le=40),
    current_user: User = Depends(get_current_user),
):
    """
    Rota de teste manual -- confirma que Query Builder + Client funcionam.
    Ainda não filtra por perfil nem passa pelo Qwen (próxima etapa).
    """
    query = build_query_from_goal(
        objetivo=objetivo, idioma_preferido=idioma, max_results=max_results
    )
    client = GoogleBooksClient()
    return client.search(query)