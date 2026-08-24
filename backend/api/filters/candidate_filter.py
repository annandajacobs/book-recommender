from api.infrastructure.google_books.schemas import BookCandidate
from api.models.reading_history import ReadingHistory


def filter_candidates(
    candidates: list[BookCandidate],
    reading_history: list[ReadingHistory],
) -> list[BookCandidate]:
    """
    Remove:
    1. Livros que o usuário já tem registrado no histórico de leitura
       (independente do status -- se já está lendo/leu/abandonou, não
       faz sentido recomendar de novo).
    2. Duplicados por id (a API do Google Books às vezes repete edições
       do mesmo livro em resultados diferentes).
    """
    ja_lidos_ids = {entry.book_id for entry in reading_history}

    vistos: set[str] = set()
    resultado: list[BookCandidate] = []

    for candidate in candidates:
        if candidate.id in ja_lidos_ids:
            continue
        if candidate.id in vistos:
            continue

        vistos.add(candidate.id)
        resultado.append(candidate)

    return resultado