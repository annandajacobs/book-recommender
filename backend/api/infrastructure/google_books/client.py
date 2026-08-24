import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from api.core.config import settings
from api.infrastructure.google_books.query_builder import (
    GoogleBooksQuery,
    build_query_from_title_author,
    build_query_from_title_author_livre,
)
from api.infrastructure.google_books.schemas import BookCandidate
from api.infrastructure.llm.schemas import DiscoveryCandidate

DESCRICAO_MAX_CHARS = 400

VALIDACAO_MAX_WORKERS = 2

RETRY_MAX_TENTATIVAS = 2
RETRY_DELAY_SEGUNDOS = 1.5

logger = logging.getLogger(__name__)


class GoogleBooksError(Exception):
    """Erro ao consultar a API do Google Books (rate limit, timeout, indisponibilidade, etc.)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GoogleBooksClient:
    def __init__(self):
        self.base_url = settings.google_books_base_url
        self.api_key = settings.google_books_api_key

    def search(self, query: GoogleBooksQuery) -> list[BookCandidate]:
        params = query.as_params()
        if self.api_key:
            params["key"] = self.api_key

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.base_url, params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GoogleBooksError(
                    "Cota da API do Google Books excedida. Configure "
                    "GOOGLE_BOOKS_API_KEY no .env ou aguarde a renovação da cota.",
                    status_code=429,
                ) from e
            if status_code >= 500:
                raise GoogleBooksError(
                    "O Google Books está temporariamente indisponível. Tente novamente "
                    "em alguns instantes.",
                    status_code=status_code,
                ) from e
            raise GoogleBooksError(f"Erro ao consultar Google Books: {e}") from e
        except httpx.TimeoutException as e:
            raise GoogleBooksError("Timeout ao consultar a API do Google Books.") from e

        data = response.json()
        items = data.get("items", [])
        return [self._parse_item(item) for item in items]

    def validar_candidatos_descoberta(
        self,
        candidatos: list[DiscoveryCandidate],
        max_results_por_candidato: int = 5,
    ) -> list[tuple[DiscoveryCandidate, list[BookCandidate]]]:
        """
        Para cada candidato "lembrado" pelo LLM na etapa de descoberta, busca no Google Books usando título+autor (query precisa, ver query_builder.build_query_from_title_author).

        Roda em paralelo (pool pequeno) porque validar 10-15 candidatos em série adicionaria vários segundos de latência por recomendação. Uma falha em um candidato individual (não encontrado, timeout, erro da API) NÃO derruba os demais -- ele simplesmente entra com lista de resultados vazia, e quem chama decide o que fazer (descartar).

        Retorna pares (candidato_original, resultados_encontrados), na mesma ordem em que os candidatos foram recebidos.
        """
        resultados: dict[int, list[BookCandidate]] = {}

        with ThreadPoolExecutor(max_workers=VALIDACAO_MAX_WORKERS) as executor:
            futuros = {
                executor.submit(
                    self._buscar_um_candidato,
                    candidato,
                    max_results_por_candidato,
                ): indice
                for indice, candidato in enumerate(candidatos)
            }

            for futuro in as_completed(futuros):
                indice = futuros[futuro]
                resultados[indice] = futuro.result()

        return [
            (candidatos[indice], resultados.get(indice, []))
            for indice in range(len(candidatos))
        ]

    def _buscar_um_candidato(
        self,
        candidato: DiscoveryCandidate,
        max_results: int,
    ) -> list[BookCandidate]:
        query = build_query_from_title_author(
            titulo=candidato.titulo,
            autor=candidato.autor,
            max_results=max_results,
        )

        for tentativa in range(1, RETRY_MAX_TENTATIVAS + 1):
            try:
                resultados = self.search(query)
                if resultados:
                    return resultados

                query_livre = build_query_from_title_author_livre(
                    titulo=candidato.titulo,
                    autor=candidato.autor,
                    max_results=max_results,
                )
                return self.search(query_livre)
            except GoogleBooksError as exc:
                eh_ultima_tentativa = tentativa == RETRY_MAX_TENTATIVAS

                deve_tentar_de_novo = (
                    exc.status_code is not None
                    and exc.status_code >= 500
                    and not eh_ultima_tentativa
                )

                if deve_tentar_de_novo:
                    logger.info(
                        "Tentativa %d falhou para '%s' (%s), tentando de novo em %.1fs...",
                        tentativa,
                        candidato.titulo,
                        candidato.autor,
                        RETRY_DELAY_SEGUNDOS,
                    )
                    time.sleep(RETRY_DELAY_SEGUNDOS)
                    continue

                logger.warning(
                    "Falha ao validar candidato '%s' (%s) no Google Books: %s",
                    candidato.titulo,
                    candidato.autor,
                    exc,
                )
                return []

        return []

    @staticmethod
    def _parse_item(item: dict) -> BookCandidate:
        volume_info = item.get("volumeInfo", {})
        autores = volume_info.get("authors", [])
        autor = ", ".join(autores) if autores else None
        image_links = volume_info.get("imageLinks", {})
        descricao = GoogleBooksClient._truncar_descricao(volume_info.get("description"))
        return BookCandidate(
            id=item.get("id", ""),
            titulo=volume_info.get("title", "Título desconhecido"),
            autor=autor,
            idioma=volume_info.get("language"),
            paginas=volume_info.get("pageCount"),
            categorias=volume_info.get("categories", []),
            descricao=descricao,
            thumbnail=image_links.get("thumbnail"),
            print_type=volume_info.get("printType"),
            average_rating=volume_info.get("averageRating"),
            ratings_count=volume_info.get("ratingsCount"),
        )

    @staticmethod
    def _truncar_descricao(descricao: str | None) -> str | None:
        if not descricao:
            return None
        if len(descricao) <= DESCRICAO_MAX_CHARS:
            return descricao
        cortado = descricao[:DESCRICAO_MAX_CHARS]
        ultimo_espaco = cortado.rfind(" ")
        if ultimo_espaco > 0:
            cortado = cortado[:ultimo_espaco]
        return cortado.rstrip(",;: ") + "..."