import json

from pydantic import ValidationError

from api.infrastructure.llm.schemas import (
    DiscoveryResult,
    RankingCandidate,
    RankingResult,
)


class LlmOutputError(Exception):
    """Levantada quando a saída do LLM é inválida ou cita livro inexistente."""


class DiscoveryOutputError(Exception):
    """Levantada quando a saída da etapa de descoberta é inválida ou vazia."""


def validate_ranking_output(raw_output: str, candidatos: list[RankingCandidate]) -> RankingResult:
    """
    Garante duas coisas antes de deixar a resposta do LLM seguir adiante:
    1. É um JSON válido no schema esperado (RankingResult).
    2. Todo 'id' citado existe de fato na lista de candidatos original --
       nunca aceitar um livro que o LLM "lembrou" e não veio da API.

    Levanta LlmOutputError se qualquer verificação falhar. Quem chama esta
    função deve decidir o que fazer (retry, ou cair no fallback determinístico).
    """
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise LlmOutputError(f"Resposta do Llm não é um JSON válido: {e}") from e

    try:
        result = RankingResult.model_validate(data)
    except ValidationError as e:
        raise LlmOutputError(f"JSON não bate com o schema esperado: {e}") from e

    ids_validos = {c.id for c in candidatos}
    ids_citados = {r.id for r in result.recomendacoes}
    ids_invalidos = ids_citados - ids_validos

    if ids_invalidos:
        raise LlmOutputError(
            f"LLM citou livro(s) que não estavam nos candidatos: {ids_invalidos}"
        )

    if not result.recomendacoes:
        raise LlmOutputError("LLM retornou lista de recomendações vazia")

    confirmados = [r for r in result.recomendacoes if r.atende_objetivo]

    if not confirmados:
        raise LlmOutputError(
            "Nenhum candidato foi marcado como atende_objetivo=True pelo LLM."
        )

    return RankingResult(recomendacoes=confirmados)


def validate_discovery_output(raw_output: str) -> DiscoveryResult:
    """
    Valida a saída da etapa de descoberta (recall).

    Diferente do ranking, aqui não há IDs para checar contra nada --
    título/autor ainda não foram confrontados com o Google Books.
    Essa validação garante só que o formato está correto e que a
    lista não é trivialmente vazia/duplicada.

    Levanta DiscoveryOutputError se o JSON for inválido, não bater com
    o schema, ou não sobrar nenhum candidato após deduplicar.
    """
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise DiscoveryOutputError(
            f"Resposta de descoberta do LLM não é um JSON válido: {e}"
        ) from e

    try:
        result = DiscoveryResult.model_validate(data)
    except ValidationError as e:
        raise DiscoveryOutputError(
            f"JSON de descoberta não bate com o schema esperado: {e}"
        ) from e

    vistos: set[tuple[str, str]] = set()
    candidatos_unicos = []

    for candidato in result.candidatos:
        titulo_norm = candidato.titulo.strip().lower()
        autor_norm = (candidato.autor or "").strip().lower()

        if not titulo_norm:
            continue

        chave = (titulo_norm, autor_norm)
        if chave in vistos:
            continue

        vistos.add(chave)
        candidatos_unicos.append(candidato)

    if not candidatos_unicos:
        raise DiscoveryOutputError(
            "LLM não retornou nenhum candidato utilizável na descoberta."
        )

    return DiscoveryResult(candidatos=candidatos_unicos)