from pydantic import BaseModel


class RankingCandidate(BaseModel):
    """
    Um candidato já filtrado + com score determinístico, pronto pro LLM avaliar
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
    status_validacao: str = "validado"
    """'validado' (título+autor batem com o Google Books) ou 'incerto'
    (achamos um registro parecido, mas a confiança do match é baixa).
    Vem do book_validator; o LLM usa isso para calibrar a justificativa."""


class RankedBook(BaseModel):
    """Um item da resposta LLM"""

    id: str
    posicao: int
    atende_objetivo: bool
    """Decisão explícita do modelo: True só se a descrição confirma o
    critério ESPECÍFICO do objetivo (não só o gênero/tom geral). O
    código usa este campo para decidir se o candidato entra na lista
    final -- não confia na justificativa em texto livre para isso."""
    justificativa: str


class RankingResult(BaseModel):
    """Resposta completa e já validada do LLM"""

    recomendacoes: list[RankedBook]


class KeywordExtractionResult(BaseModel):
    """Resultado da extração de palavras-chave de um objetivo descritivo.

    Mantido apenas para o pipeline legado (fallback caso a descoberta
    semântica falhe).
    """

    keywords: list[str]


class DiscoveryCandidate(BaseModel):
    """
    Um palpite de livro feito pelo LLM na etapa de descoberta.

    Não é confiável ainda -- título e autor podem ser alucinados.
    Precisa passar pela validação no Google Books antes de virar
    um RankingCandidate.
    """

    titulo: str
    autor: str | None = None


class DiscoveryResult(BaseModel):
    """Resposta completa e já validada (schema) da etapa de descoberta."""

    candidatos: list[DiscoveryCandidate]