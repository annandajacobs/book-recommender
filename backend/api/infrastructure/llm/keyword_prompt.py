import json

SYSTEM_PROMPT_KEYWORDS = """Você extrai palavras-chave de busca a partir de um objetivo \
de leitura descrito livremente pelo usuário.

O objetivo pode ser curto e direto ("aprender python") ou uma descrição narrativa \
longa ("uma história de amor em que os personagens se odeiam no início mas depois \
se apaixonam"). Sua tarefa é destilar esse texto em 3 a 5 palavras-chave ou expressões \
curtas que funcionem bem como termos de busca em um catálogo de livros.

Você pode incluir: gênero literário, tema, estilo, período, e -- se tiver certeza \
de que existe -- até um título ou autor real que combine bem com o pedido. Não tem \
problema se você não tiver certeza absoluta do título/autor: essas palavras-chave \
serão usadas apenas para BUSCAR em um catálogo real, então uma sugestão imprecisa \
apenas não retornará resultado, não causa nenhum dano.

Responda SOMENTE com um JSON no formato:
{"keywords": ["termo 1", "termo 2", "termo 3"]}
"""


def build_keyword_extraction_prompt(objetivo: str) -> tuple[str, str]:
    user_prompt = json.dumps({"objetivo": objetivo}, ensure_ascii=False)
    return SYSTEM_PROMPT_KEYWORDS, user_prompt