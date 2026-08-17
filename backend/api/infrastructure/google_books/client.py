import httpx

from api.core.config import settings
from api.infrastructure.google_books.query_builder import GoogleBooksQuery
from api.infrastructure.google_books.schemas import BookCandidate

DESCRICAO_MAX_CHARS = 400


class GoogleBooksClient:
    def __init__(self):
        self.base_url = settings.google_books_base_url
        self.api_key = settings.google_books_api_key

    def search(self, query: GoogleBooksQuery) -> list[BookCandidate]:
        params = query.as_params()
        if self.api_key:
            params["key"] = self.api_key

        with httpx.Client(timeout=10.0) as client:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        return [self._parse_item(item) for item in items]

    @staticmethod
    def _parse_item(item: dict) -> BookCandidate:
        """
        A resposta do Google Books é irregular -- nem todo livro tem todos
        os campos. Todo acesso aqui é defensivo (.get com default) para
        nunca quebrar por causa de metadado ausente.
        """
        volume_info = item.get("volumeInfo", {})

        autores = volume_info.get("authors", [])
        autor = ", ".join(autores) if autores else None

        image_links = volume_info.get("imageLinks", {})

        descricao_bruta = volume_info.get("description")
        descricao = GoogleBooksClient._truncar_descricao(descricao_bruta)

        return BookCandidate(
            id=item.get("id", ""),
            titulo=volume_info.get("title", "Título desconhecido"),
            autor=autor,
            idioma=volume_info.get("language"),
            paginas=volume_info.get("pageCount"),
            categorias=volume_info.get("categories", []),
            descricao=descricao,
            thumbnail=image_links.get("thumbnail"),
        )

    @staticmethod
    def _truncar_descricao(descricao: str | None) -> str | None:
        """
        Reduz o tamanho da descrição antes dela circular pelo resto do sistema
        (e eventualmente pelo prompt do Qwen). Corta em um espaço para não
        quebrar palavra no meio.
        """
        if not descricao:
            return None

        if len(descricao) <= DESCRICAO_MAX_CHARS:
            return descricao

        cortado = descricao[:DESCRICAO_MAX_CHARS]
        ultimo_espaco = cortado.rfind(" ")
        if ultimo_espaco > 0:
            cortado = cortado[:ultimo_espaco]

        return cortado.rstrip(",;: ") + "..."