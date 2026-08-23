import json

from pydantic import ValidationError

from api.infrastructure.gemma.schemas import RankingCandidate, RankingResult


class GemmaOutputError(Exception):
    """Levantada quando a saída do Gemma é inválida ou cita livro inexistente."""


def validate_ranking_output(raw_output: str, candidatos: list[RankingCandidate]) -> RankingResult:
    """
    Garante duas coisas antes de deixar a resposta do Gemma seguir adiante:
    1. É um JSON válido no schema esperado (RankingResult).
    2. Todo 'id' citado existe de fato na lista de candidatos original --
       nunca aceitar um livro que o Gemma "lembrou" e não veio da API.

    Levanta GemmaOutputError se qualquer verificação falhar. Quem chama esta
    função deve decidir o que fazer (retry, ou cair no fallback determinístico).
    """
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise GemmaOutputError(f"Resposta do Gemma não é um JSON válido: {e}") from e

    try:
        result = RankingResult.model_validate(data)
    except ValidationError as e:
        raise GemmaOutputError(f"JSON não bate com o schema esperado: {e}") from e

    ids_validos = {c.id for c in candidatos}
    ids_citados = {r.id for r in result.recomendacoes}
    ids_invalidos = ids_citados - ids_validos

    if ids_invalidos:
        raise GemmaOutputError(
            f"Gemma citou livro(s) que não estavam nos candidatos: {ids_invalidos}"
        )

    if not result.recomendacoes:
        raise GemmaOutputError("Gemma retornou lista de recomendações vazia")

    return result