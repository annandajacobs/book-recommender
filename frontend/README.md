# Estante — frontend

Interface web para o Book Recommender: login/cadastro, objetivos de leitura,
preferências de gênero, recomendações e histórico de leitura.

## Rodando localmente

```bash
npm install
cp .env.example .env   # ajuste VITE_API_URL se a API não estiver em localhost:8000
npm run dev
```

Abre em `http://localhost:5173`.

## Pré-requisito no backend

O backend precisa aceitar requisições vindas de `http://localhost:5173` via
CORS. Confirme em `backend/main.py` que `CORSMiddleware` está registrado com
essa origem antes de subir a API (`uvicorn main:app --reload`).

## Estrutura

```
src/
  api/client.js        # wrapper de fetch + autenticação (Bearer token)
  context/AuthContext   # estado de sessão (login/registro/logout)
  components/            # Layout, BookCard, Loader, EmptyState, ProtectedRoute
  pages/
    LoginPage / RegisterPage
    GoalsPage            # objetivos de leitura (POST/GET/PATCH/DELETE /goals)
    PreferencesPage       # pesos por gênero (POST/GET/PATCH/DELETE /preferences)
    RecommendationsPage   # GET /recommendations — tela principal
    HistoryPage            # POST/GET/PATCH/DELETE /reading-history
  index.css              # design system (tokens, componentes)
```

## Design

Paleta de papel e capa de livro (verde pano de encadernação, dourado de
folha de rosto), tipografia Fraunces (display) + Inter (corpo) + IBM Plex
Mono (dados: scores, ids, datas). Sem framework de CSS — os tokens estão
centralizados em `src/index.css` via custom properties.
