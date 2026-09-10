# Book Recommender

Sistema de recomendação de leitura que utiliza um LLM para descoberta semântica de candidatos e o Google Books para validação de existência e metadados. A aplicação possui uma interface conversacional em React para coletar objetivos e preferências de leitura.

O sistema descobre e valida sugestões de livros, combinando um
LLM (descoberta semântica) com o catálogo do Google Books, com um fallback por palavras-chave quando a descoberta semântica não retorna nada.

Monorepo com duas partes:

```
book-recommender/
  backend/    # API REST (FastAPI + SQLAlchemy)
  frontend/   # SPA em React (Vite) — interface conversacional para o recomendador
```

## Como funciona, em resumo

1. O usuário se cadastra/loga (`/api/v1/auth`).
2. Conta um **objetivo de leitura** (ex.: "aprender python", "ler um romance
   envolvente") e, opcionalmente, o **nível de conhecimento** no assunto.
3. Pode adicionar **preferências de gênero** (peso por gênero) para refinar
   os resultados.
4. O backend utiliza o contexto do usuário para **descobrir candidatos** semanticamente via LLM. Os candidatos são então **validados** contra
   o Google Books (existe? dados batem?) e
   **ranqueados** por regras determinísticas (`GET /api/v1/recommendations`).
5. Livros aceitos podem ser marcados no **histórico de leitura**
   (`/api/v1/reading-history`), com status (lendo, lido, etc.).

No frontend, o fluxo de recomendação é apresentado por meio de uma interface conversacional (ver seção [Frontend](#frontend) abaixo). A API permanece REST e recebe operações estruturadas, como criação de objetivos e preferências. O LLM é utilizado no backend especificamente para a descoberta semântica dos livros, e não para interpretar cada mensagem da conversa.

## Backend

**Stack:** FastAPI, SQLAlchemy (ORM), Pydantic (schemas de entrada/saída),
`uv` como gerenciador de pacotes/ambiente, `ruff` para lint.

### Estrutura (`backend/api/`)

```
api/
  database/                 # engine, Base, sessão
  models/                   # User, UserGoal, UserPreference, ReadingHistory
  schemas/                  # contratos Pydantic (request/response)
  domain/
    scoring.py               # ranqueamento dos candidatos
  filters/
    candidate_filter.py      # filtragem de candidatos do LLM
  infrastructure/
    llm/                     # prompts de descoberta, validação da saída do LLM
    google_books/            # client, query builder, validação de metadados
  services/
    recommendation_service.py  # orquestra: descoberta -> validação -> ranking
  routers/                  # auth, goals, preferences, recommendations, reading-history
main.py                     # app FastAPI, CORS, registro de routers
```

### Rodando localmente

> Confirme estes comandos contra o `pyproject.toml` / scripts do projeto —
> assumindo o padrão `uv` + `uvicorn`:

```bash
docker compose up -d postgres
cd backend
uv sync
cp .env.example .env   # preencha as chaves necessárias (ver abaixo)
uv run uvicorn main:app --reload
```

API disponível em `http://localhost:8000` (docs interativos em
`http://localhost:8000/docs`).

### Variáveis de ambiente

Ver `backend/.env.example` para a lista completa. Em linhas gerais, espere
precisar configurar:
- Conexão com o banco de dados
- Chave de API do provedor de LLM usado na descoberta
- Chave de API do Google Books (se exigida pelo endpoint usado)
- Segredo/algoritmo de JWT para autenticação

### CORS

O frontend roda em `http://localhost:5173` por padrão. Confirme em
`backend/main.py` que essa origem está liberada no `CORSMiddleware` antes
de subir os dois juntos.

### Lint

```bash
cd backend
uv run ruff check .          # lint
uv run ruff check . --fix    # corrige o que for automático (ex.: ordenação de imports)
```

O CI roda `uv run ruff check .` — rode localmente antes de commitar para
evitar quebra de pipeline.

## Frontend

**Stack:** React 18 + Vite, `react-router-dom` para rotas, sem framework de
CSS (design tokens próprios via custom properties).

### Rodando localmente

```bash
cd frontend
npm install
cp .env.example .env   # ajuste VITE_API_URL se a API não estiver em localhost:8000
npm run dev
```

Abre em `http://localhost:5173`.

### Estrutura

```
src/
  api/client.js          # wrapper de fetch + autenticação (Bearer token)
  context/AuthContext     # estado de sessão (login/registro/logout)
  components/
    Layout, BookCard, Loader, EmptyState, ProtectedRoute
    chat/                 # MessageBubble, ChatComposer — bolhas e input da conversa
  pages/
    LoginPage / RegisterPage
    RecommendationsPage    # "Conversa" — tela principal, fluxo conversacional
    GoalsPage               # "Meus pedidos" — histórico de objetivos já pedidos
    PreferencesPage          # pesos por gênero
    HistoryPage               # status de leitura dos livros marcados
  index.css                 # design system (tokens, bolhas de chat, componentes)
```

### Como funciona a interface conversacional

A tela principal utiliza uma interface conversacional para transformar a interação com o sistema de recomendação em uma sequência de mensagens. A conversa, porém, não é conduzida por um agente de IA: as ações disponíveis são determinadas pela interface e convertidas em chamadas à API REST.

O texto digitado pode ser enviado em dois modos:
- **Objetivo** (padrão): cria um novo objetivo de leitura e solicita recomendações.
- **Gênero**: cria uma preferência de gênero e refaz a busca considerando
  o gênero atual.

Objetivos antigos ficam disponíveis em **Meus pedidos**, de onde dá para
retomar qualquer um deles ("Retomar e buscar recomendações"), reativando-o
e disparando a busca na hora.

### Design

Paleta de papel e capa de livro (verde pano de encadernação, dourado de
folha de rosto), tipografia Fraunces (display) + Inter (corpo) + IBM Plex
Mono (dados: scores, ids, datas). Tokens centralizados em `src/index.css`.

## Qualidade do recomendador

Medimos métricas objetivas (completude, taxa de fallback, latência, taxa de
recomendações com status "incerto") rodando o pipeline real contra um
conjunto pequeno de objetivos de exemplo. **Isto não é um benchmark com
gabarito de livros esperados** — validar se as recomendações são de fato
boas (relevância de conteúdo) é o Grupo 2, ainda não implementado; o que
temos hoje mede comportamento do pipeline (falha, completa, é rápido?),
não qualidade editorial.

### Limitação de hardware e modelo

Este projeto roda o LLM localmente via Ollama, em hardware de
desenvolvimento pessoal (sem GPU dedicada/servidor de inferência). Por
isso, o modelo usado é intencionalmente pequeno — `llama3.2:3b` — em vez
de um modelo maior que teria mais capacidade de seguir instruções e
avaliar candidatos com mais consistência.

Isso tem uma consequência direta e esperada nos números abaixo: **modelo
menor = mais falhas de reranking, mais fallback pra score determinístico,
e mais recomendações com status "incerto"**. As taxas de fallback e de
incertos medidas aqui não devem ser lidas como "o pipeline tem um bug" —
são, em boa parte, o custo de rodar um modelo de 3B parâmetros em vez de
um modelo maior. Se o projeto puder rodar contra um modelo maior (local
com mais recursos, ou via API de um provedor), espera-se que essas taxas
melhorem sem precisar mudar nada na lógica do `RecommendationService`.

### Última medição

[evals/results/group1_2026-09-10.md](evals/results/group1_2026-09-10.md)
— commit `727a19e`, modelo `llama3.2:3b`, **n=1 execução por objetivo**.

⚠️ Amostra pequena: rode com `--runs 5` ou mais antes de usar esses
números pra qualquer decisão — o LLM não é determinístico, e n=1 por
objetivo é só um retrato pontual, não uma medição estável.

Resumo daquela rodada (ver o link acima para o relatório completo, por
objetivo):

| Métrica | Valor |
|---|---|
| Completude média | 79.2% |
| Taxa de fallback | 25.0% |
| Recomendações "incerto" | 21.1% |
| Tempo p50 / p95 | 38s / 49s |

### Como rodar

```bash
uv run python -m evals.run_group1_metrics --runs 5 --eu-sei-que-isso-usa-o-banco-configurado
```

Aponte `POSTGRES_DB` (e demais variáveis de `api/core/config.py`) para um
banco de teste, não o de desenvolvimento — o script cria e apaga um
usuário fake por execução. Ver o docstring do script para detalhes de
custo/tokens e das ressalvas de cada métrica.

## Limitações conhecidas

- A interface conversacional ainda não possui interpretação de linguagem natural para inferir automaticamente a intenção do usuário. O tipo da entrada é definido pelo modo selecionado no composer (objetivo ou gênero).
- Não há checagem de duplicidade de objetivo nem validação do que é
  digitado como "gênero" (aceita qualquer texto).
- Recomendações não são persistidas — cada busca é recalculada na hora;
  o que fica salvo é apenas o objetivo/preferência que gerou a busca.

## Próximos passos possíveis

- Validação/normalização de gênero (lista conhecida + confirmação para
  texto fora do padrão).
- Regra de "objetivo ativo único" garantida no backend, não só no
  frontend.
- Camada de interpretação de linguagem natural: adicionar um endpoint de interpretação (/chat) capaz de transformar mensagens livres em uma estrutura de intenção, objetivo, nível e preferências antes de acionar o pipeline de recomendação.