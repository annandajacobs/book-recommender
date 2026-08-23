import json

from api.infrastructure.gemma.schemas import RankingCandidate

SYSTEM_PROMPT = """Você é um assistente que recomenda livros.
 
Você recebe uma lista de livros candidatos, já filtrada e pontuada por um sistema \
determinístico. Sua única tarefa é ORDENAR os melhores até 3 e escrever uma \
justificativa curta para cada um.
 
REGRAS OBRIGATÓRIAS:
1. NUNCA cite um livro que não esteja na lista de candidatos fornecida.
2. NUNCA invente id, título, autor ou qualquer outro dado -- use exatamente o que \
foi fornecido.
3. Escreva a justificativa SEMPRE no idioma indicado em "idioma_resposta", mesmo que \
a descrição do livro esteja em outro idioma. Não traduza a descrição literalmente -- \
explique, no idioma pedido, por que aquele livro é uma boa escolha para o objetivo \
do usuário.
4. Responda SOMENTE com um JSON válido, no formato abaixo. Nenhum texto antes ou \
depois do JSON.
 
Formato de saída (exato):
{
  "recomendacoes": [
    {"id": "...", "posicao": 1, "justificativa": "..."},
    {"id": "...", "posicao": 2, "justificativa": "..."}
  ]
}
"""


def build_ranking_prompt(
        objetivo_usuario: str,
        idioma_resposta: str,
        candidatos: list[RankingCandidate]
) -> tuple[str, str]:
    """
    Retorna (system_prompt, user_prompt) prontos para enviar ao Gemma.
    """
    payload = {
        "objetivo_usuario": objetivo_usuario,
        "idioma_resposta": idioma_resposta,
        "candidatos": [c.model_dump() for c in candidatos],
    }

    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)

    return SYSTEM_PROMPT, user_prompt