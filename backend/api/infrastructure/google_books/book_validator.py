import re
import unicodedata
from difflib import SequenceMatcher
from enum import Enum

from api.infrastructure.google_books.schemas import BookCandidate
from api.infrastructure.llm.schemas import DiscoveryCandidate

TITULO_THRESHOLD_FORTE = 0.82
AUTOR_THRESHOLD_FORTE = 0.65

TITULO_THRESHOLD_FRACO = 0.5


class MatchStatus(str, Enum):
    VALIDADO = "validado"
    INCERTO = "incerto"
    DESCARTADO = "descartado"


class ValidatedBook:
    """Resultado da validação: o BookCandidate real + o veredito."""

    def __init__(self, book: BookCandidate, status: MatchStatus):
        self.book = book
        self.status = status


def _normalizar(texto: str) -> str:
    """
    minúsculas, sem acento, sem pontuação, espaços colapsados.
    """
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _similaridade(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalizar(a), _normalizar(b)).ratio()


def _melhor_similaridade_autor(autor_candidato: str | None, autor_resultado: str | None) -> float:
    """
    O Google Books às vezes retorna vários autores separados por vírgula. 
    Comparamos o autor do candidato contra CADA autor do resultado e ficamos com o melhor match, em vez de comparar a string inteira.
    """
    if not autor_candidato or not autor_resultado:
        return 0.0

    autores_resultado = [a.strip() for a in autor_resultado.split(",") if a.strip()]
    if not autores_resultado:
        return 0.0

    return max(_similaridade(autor_candidato, autor) for autor in autores_resultado)


def validate_book_match(
    candidato: DiscoveryCandidate,
    resultados: list[BookCandidate],
) -> ValidatedBook | None:
    """
    Recebe um candidato "lembrado" pelo LLM e a lista de resultados que o Google Books retornou para ele (pode ser vazia).

    Não confia cegamente no primeiro resultado: o Google pode devolver uma edição, tradução ou obra apenas parecida. Escolhe, entre os
    resultados, o que tem a MELHOR similaridade de título (com
    critério de desempate por similaridade de autor), e só aceita se passar de um threshold mínimo.

    Retorna None se nenhum resultado bater o suficiente para ser considerado sequer INCERTO (ou seja: DESCARTAR o candidato).
    """
    if not resultados:
        return None

    melhor: tuple[float, float, BookCandidate] | None = None

    for resultado in resultados:
        sim_titulo = _similaridade(candidato.titulo, resultado.titulo)
        sim_autor = _melhor_similaridade_autor(candidato.autor, resultado.autor)

        if melhor is None or sim_titulo > melhor[0]:
            melhor = (sim_titulo, sim_autor, resultado)

    sim_titulo, sim_autor, resultado = melhor

    if sim_titulo >= TITULO_THRESHOLD_FORTE and sim_autor >= AUTOR_THRESHOLD_FORTE:
        return ValidatedBook(resultado, MatchStatus.VALIDADO)

    if sim_titulo >= TITULO_THRESHOLD_FORTE and not candidato.autor:
        return ValidatedBook(resultado, MatchStatus.VALIDADO)

    if sim_titulo >= TITULO_THRESHOLD_FRACO:
        return ValidatedBook(resultado, MatchStatus.INCERTO)

    return None