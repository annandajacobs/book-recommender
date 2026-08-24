import json

from pydantic import ValidationError

from api.infrastructure.llm.schemas import KeywordExtractionResult


class KeywordExtractionError(Exception):
    """Levantada quando a extração de palavras-chave falha (JSON inválido, vazio, etc.)."""


def validate_keyword_output(raw_output: str) -> KeywordExtractionResult:
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise KeywordExtractionError(f"Resposta não é um JSON válido: {e}") from e

    try:
        result = KeywordExtractionResult.model_validate(data)
    except ValidationError as e:
        raise KeywordExtractionError(f"JSON não bate com o schema esperado: {e}") from e

    if not result.keywords:
        raise KeywordExtractionError("Nenhuma palavra-chave foi extraída")

    return result