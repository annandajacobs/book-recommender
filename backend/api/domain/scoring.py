from api.infrastructure.google_books.schemas import BookCandidate
from api.models.user_preference import UserPreference

PESO_IDIOMA = 1.0
PESO_GENERO_BASE = 4.0
PESO_AVALIACAO = 3.0

NOTA_MINIMA_PARA_BONUS = 3.5
NOTA_MINIMA_ACEITAVEL = 3.0
RATINGS_COUNT_MINIMO_CONFIAVEL = 5
PENALIDADE_AVALIACAO_RUIM = -2.0


def score_candidate(
    candidate: BookCandidate,
    idioma_preferido: str | None,
    preferencias: list[UserPreference],
) -> tuple[float, str]:
    """
    Calcula um score determinístico e uma explicação curta.
    Não usa LLM -- é a base objetiva que o Qwen recebe para ancorar seu
    julgamento, em vez de avaliar do zero.
    """
    score = 1.0
    motivos = []

    if idioma_preferido and candidate.idioma:
        idioma_candidato = candidate.idioma.split("-")[0].lower()
        idioma_alvo = idioma_preferido.split("-")[0].lower()

        if idioma_candidato == idioma_alvo:
            score += PESO_IDIOMA
            motivos.append("idioma compatível")
        else:
            motivos.append(f"idioma diferente do preferido ({candidate.idioma})")

    categorias_candidato = {c.lower() for c in candidate.categorias}
    for pref in preferencias:
        genero_lower = pref.genero.lower()
        if any(genero_lower in cat or cat in genero_lower for cat in categorias_candidato):
            score += PESO_GENERO_BASE * pref.peso
            motivos.append(f"match com gênero favorito '{pref.genero}'")

    if candidate.average_rating is not None and candidate.ratings_count is not None:
        if (
            candidate.ratings_count >= RATINGS_COUNT_MINIMO_CONFIAVEL
            and candidate.average_rating < NOTA_MINIMA_ACEITAVEL
        ):
            score += PENALIDADE_AVALIACAO_RUIM
            motivos.append(
                f"avaliação baixa ({candidate.average_rating}★, "
                f"{candidate.ratings_count} avaliações)"
            )
        elif candidate.average_rating >= NOTA_MINIMA_PARA_BONUS:
            proporcao = (candidate.average_rating - NOTA_MINIMA_PARA_BONUS) / (
                5.0 - NOTA_MINIMA_PARA_BONUS
            )
            score += PESO_AVALIACAO * proporcao
            motivos.append(
                f"bem avaliado ({candidate.average_rating}★, "
                f"{candidate.ratings_count} avaliações)"
            )

    motivo_final = "; ".join(motivos) if motivos else "sem matches fortes de perfil"

    return round(score, 2), motivo_final
