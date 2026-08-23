from pydantic import BaseModel


class BookCandidate(BaseModel):
    """
    Representação normalizada de um livro, independente do formato bruto
    da API do Google Books. O resto do sistema (filtros, scoring, Gemma)
    trabalha só com este schema.
    """

    id: str
    titulo: str
    autor: str | None = None
    idioma: str | None = None
    paginas: int | None = None
    categoria: list[str] = []
    descricao: str | None = None
    thumbnail: str | None = None