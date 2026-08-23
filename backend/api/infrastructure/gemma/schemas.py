from pydantic import BaseModel


class RankingCandidate(BaseModel):
    """
    Um candidato já filtrado + com score determinístico, pronto pro Gemma avaliar
    """

    id: str
    titulo: str
    autor: str | None = None
    idioma: str | None = None
    paginas: int | None = None
    categorias: list[str] = []
    descricao: str | None = None
    score_deterministico: float
    motivo_score: str


class RankedBook(BaseModel):
    """Um item da resposta Gemma"""

    id: str
    posicao: int
    justificativa: str


class RankingResult(BaseModel):
    """Resposta completa e já validada do Gemma"""

    recomendacoes: list[RankedBook]
