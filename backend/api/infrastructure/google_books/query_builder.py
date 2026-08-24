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
    fica a cargo do LLM, fora desta camada.
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


def build_query_from_title_author(
    titulo: str,
    autor: str | None = None,
    max_results: int = 5,
) -> GoogleBooksQuery:
    """
    Monta uma query de VALIDAÇÃO: usada para confirmar se um livro que
    o LLM "lembrou" (etapa de descoberta) existe de fato.

    Usa os operadores intitle:/inauthor: do Google Books, que são bem
    mais precisos que uma busca de texto livre -- reduz falsos
    positivos (ex.: outro livro que só compartilha uma palavra do
    título).

    IMPORTANTE: título e autor vão entre aspas na query. Sem aspas,
    intitle:/inauthor: só se aplicam à PRIMEIRA palavra seguinte (é
    assim que a API do Google Books interpreta o operador) -- um
    título como "O Senhor dos Anéis: A Companhia do Anel" viraria, na
    prática, uma busca restrita só por "O" (a primeira palavra), com
    o resto solto como texto livre. Com aspas, o operador vale pra
    frase inteira.

    Sem lang_restrict de propósito: restringir por idioma aqui poderia
    descartar um livro real só porque a edição indexada está em outro
    idioma. O filtro de idioma do usuário continua valendo depois,
    no scoring/ranking.
    """
    titulo_limpo = titulo.strip().replace('"', "")
    termos = [f'intitle:"{titulo_limpo}"']

    if autor:
        autor_limpo = autor.strip().replace('"', "")
        termos.append(f'inauthor:"{autor_limpo}"')

    q = " ".join(termos)

    return GoogleBooksQuery(
        q=q,
        max_results=max_results,
    )


def build_query_from_title_author_livre(
    titulo: str,
    autor: str | None = None,
    max_results: int = 5,
) -> GoogleBooksQuery:
    """
    Fallback de RECALL para quando build_query_from_title_author não
    encontra nada. Usa texto livre em vez de intitle:/inauthor:, que
    são operadores rígidos e podem falhar com pequenas diferenças de
    grafia/transliteração (ex.: "Ilyich" vs "Ilitch", "Leo Tolstói"
    vs "Liev Tolstói"). O Google Books faz relevância mais tolerante
    em busca de texto livre do que na busca por operador exato.

    Menos preciso que a busca estruturada -- por isso só deve ser
    usada como segunda tentativa, nunca como primeira.
    """
    termos = [titulo.strip()]

    if autor:
        termos.append(autor.strip())

    q = " ".join(termos)

    return GoogleBooksQuery(
        q=q,
        max_results=max_results,
    )
