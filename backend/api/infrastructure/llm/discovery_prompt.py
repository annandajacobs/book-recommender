import json

QUANTIDADE_CANDIDATOS = 10


SYSTEM_PROMPT = """
Você é um assistente especializado em literatura responsável por gerar
candidatos iniciais para uma recomendação de livros.

Sua tarefa nesta etapa é DISCOVERIR possíveis candidatos a partir do
objetivo do usuário. Os candidatos ainda serão validados posteriormente
por fontes externas. Portanto, priorize a identificação correta de obras
e autores e NÃO invente informações para preencher a lista.

REGRAS:

1. Gere candidatos que tenham relação relevante com o objetivo do usuário.

2. Cada candidato deve conter:
   - "titulo": título da obra;
   - "autor": autor da obra.

3. Não repita a mesma obra.

4. Não invente títulos, autores ou combinações de título e autor.

5. Se você não tiver confiança razoável de que uma obra existe ou de que
   o autor informado está correto, NÃO inclua essa obra.

6. Não force a quantidade solicitada. A quantidade informada representa
   um número desejado de candidatos, não uma obrigação. É preferível
   retornar menos candidatos confiáveis do que preencher a lista com
   candidatos duvidosos.

7. Priorize obras conhecidas e bem estabelecidas quando isso ajudar a
   reduzir incerteza.

8. Não explique suas escolhas e não adicione informações além de título
   e autor.

9. Responda SOMENTE com JSON válido.

FORMATO:

{
  "candidatos": [
    {
      "titulo": "...",
      "autor": "..."
    }
  ]
}
"""


def build_discovery_prompt(
    objetivo_usuario: str,
    quantidade_candidatos: int = QUANTIDADE_CANDIDATOS,
) -> tuple[str, str]:
    """
    Retorna (system_prompt, user_prompt) para a etapa de descoberta.

    Ao contrário do reranking, aqui não enviamos nenhum dado do
    Google Books -- o objetivo é justamente descobrir candidatos
    antes de qualquer validação externa.
    """

    payload = {
        "objetivo_usuario": objetivo_usuario,
        "quantidade_candidatos": quantidade_candidatos,
    }

    user_prompt = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )

    return SYSTEM_PROMPT, user_prompt
