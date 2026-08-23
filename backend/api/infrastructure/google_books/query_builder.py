class GoogleBooksQuery:
    """
    Representa uma query já pronta para a API do Google Books:
    q = termo de busca (pode usar operadores tipo subject:, intitle:, inauthor:)
    lang_restrict = filtro de idioma (ISO 639-1: 'pt', 'en'...)
    max_results = quantos candidatos pedir (1-40, limite da API)
    """

    def __init__(self, q: str, lang_restrict: str | None = None, max_results: int = 20):
        self.q = q
        self.lang_restrict = lang_restrict
        self.max_results = max_results

    def as_params(self) -> dict:
        params = {"q": self.q, "maxResults": self.max_results}
        if self.lang_restrict:
            params["langRestrict"] = self.lang_restrict
        return params


def build_query_from_goal(
    objetivo: str,
    idioma_preferido: str | None = None,
    generos: list[str] | None = None,
    max_results: int = 20,
) -> GoogleBooksQuery:
    """
    Monta uma query objetiva a partir do objetivo de leitura do usuário
    (ex: "aprender python") e, opcionalmente, gêneros favoritos.

    Não interpreta linguagem natural de forma alguma -- é concatenação
    determinística. Interpretação de texto livre (se um dia precisar)
    fica a cargo do Gemma, fora desta camada.
    """
    termos = [objetivo.strip()]

    if generos:
        termos.extend(f"subject:{genero.strip()}" for genero in generos)

    q = " ".join(termos)

    return GoogleBooksQuery(
        q=q,
        lang_restrict=idioma_preferido,
        max_results=max_results,
    )