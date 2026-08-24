from pydantic import BaseModel


class RecommendedBook(BaseModel):
    id: str
    titulo: str
    autor: str | None = None
    thumbnail: str | None = None
    categorias: list[str] = []
    average_rating: float | None = None
    ratings_count: int | None = None
    posicao: int
    score_deterministico: float
    justificativa: str
    status_validacao: str = "validado"


class RecommendationOut(BaseModel):
    objetivo: str
    recomendacoes: list[RecommendedBook]
    fallback_usado: bool = False
    pipeline: str = "descoberta"
    """'descoberta' (LLM descobre -> Google Books valida -> LLM
    reordena) ou 'legado' (busca por keywords, usado quando a
    descoberta semântica falha)."""