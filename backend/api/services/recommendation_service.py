import logging
from difflib import SequenceMatcher

import httpx
from sqlalchemy.orm import Session

from api.domain.scoring import score_candidate
from api.filters.candidate_filter import filter_candidates
from api.infrastructure.google_books.book_validator import (
    MatchStatus,
    ValidatedBook,
    validate_book_match,
)
from api.infrastructure.google_books.client import GoogleBooksClient
from api.infrastructure.google_books.query_builder import build_query_from_goal
from api.infrastructure.google_books.schemas import BookCandidate
from api.infrastructure.llm.client import LlmClient
from api.infrastructure.llm.discovery_prompt import build_discovery_prompt
from api.infrastructure.llm.keyword_prompt import build_keyword_extraction_prompt
from api.infrastructure.llm.keyword_validator import (
    KeywordExtractionError,
    validate_keyword_output,
)
from api.infrastructure.llm.output_validator import (
    DiscoveryOutputError,
    LlmOutputError,
    validate_discovery_output,
    validate_single_candidate_output,
)
from api.infrastructure.llm.prompts import build_single_candidate_prompt
from api.infrastructure.llm.schemas import DiscoveryResult, RankingCandidate
from api.models.reading_history import ReadingHistory
from api.models.user import User
from api.models.user_goal import UserGoal
from api.models.user_preference import UserPreference
from api.schemas.recommendation import RecommendationOut, RecommendedBook

logger = logging.getLogger(__name__)


CANDIDATOS_PARA_LLM = 8

CANDIDATOS_DA_API = 40

RECOMENDACOES_FINAIS = 3


class NoBooksFoundError(Exception):
    """Nenhum candidato sobrou depois dos filtros, em nenhum dos pipelines."""


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.google_books = GoogleBooksClient()
        self.llm = LlmClient()

    def recommend(
        self,
        user: User,
        goal: UserGoal,
    ) -> RecommendationOut:

        preferencias = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user.id)
            .all()
        )

        reading_history = (
            self.db.query(ReadingHistory)
            .filter(ReadingHistory.user_id == user.id)
            .all()
        )

        try:
            candidatos_validados = self._descobrir_e_validar(goal.objetivo)
        except (DiscoveryOutputError, httpx.HTTPError) as exc:
            logger.warning(
                "Etapa de descoberta falhou. Caindo para pipeline legado: %s",
                exc,
            )
            return self._recommend_legado(
                user=user,
                goal=goal,
                preferencias=preferencias,
                reading_history=reading_history,
            )

        candidatos_novos = filter_candidates(
            [validado.book for validado in candidatos_validados],
            reading_history,
        )

        status_por_id = {
            validado.book.id: validado.status for validado in candidatos_validados
        }

        logger.info(
            "%d candidatos validados restaram após o filtro de histórico.",
            len(candidatos_novos),
        )

        if not candidatos_novos:
            logger.warning(
                "Nenhum candidato validado sobrou (tudo já lido, ou nada "
                "confirmado no Google Books). Caindo para pipeline legado."
            )
            return self._recommend_legado(
                user=user,
                goal=goal,
                preferencias=preferencias,
                reading_history=reading_history,
            )

        pontuados = [
            (candidate, *score_candidate(candidate, user.idioma_preferido, preferencias))
            for candidate in candidatos_novos
        ]
        pontuados.sort(key=lambda item: item[1], reverse=True)

        top_candidatos = pontuados[:CANDIDATOS_PARA_LLM]

        candidatos_por_id: dict[str, BookCandidate] = {
            candidate.id: candidate for candidate, _, _ in top_candidatos
        }

        ranking_candidates = [
            RankingCandidate(
                id=candidate.id,
                titulo=candidate.titulo,
                autor=candidate.autor,
                idioma=candidate.idioma,
                paginas=candidate.paginas,
                categorias=candidate.categorias,
                descricao=candidate.descricao,
                score_deterministico=score,
                motivo_score=motivo,
                status_validacao=status_por_id.get(candidate.id, MatchStatus.VALIDADO).value,
            )
            for candidate, score, motivo in top_candidatos
        ]

        try:
            resultado_final = self._recomendar_via_llm(
                goal=goal,
                idioma_resposta=user.idioma_preferido or "pt",
                ranking_candidates=ranking_candidates,
                candidatos_por_id=candidatos_por_id,
            )
            fallback_usado = False
        except (LlmOutputError, httpx.HTTPError) as exc:
            logger.warning(
                "Reranking falhou. Usando fallback por score: %s",
                exc,
            )
            resultado_final = self._fallback_por_score(top_candidatos)
            fallback_usado = True

        return RecommendationOut(
            objetivo=goal.objetivo,
            recomendacoes=resultado_final,
            fallback_usado=fallback_usado,
            pipeline="descoberta",
        )


    def _descobrir_e_validar(self, objetivo: str) -> list[ValidatedBook]:
        """
        1. Pede ao LLM uma lista de candidatos (título + autor),
           sem nenhum dado externo -- é uma etapa de RECALL.
        2. Confirma cada candidato no Google Books (em paralelo).
        3. Descarta o que não bateu; mantém 'validado' e 'incerto'.

        Levanta DiscoveryOutputError/httpx.HTTPError se a chamada ao
        LLM falhar -- quem chama decide cair no pipeline legado.
        """
        system_prompt, user_prompt = build_discovery_prompt(objetivo)

        raw_output = self.llm.chat_json(system_prompt, user_prompt)

        descoberta: DiscoveryResult = validate_discovery_output(raw_output)

        logger.info(
            "LLM sugeriu %d candidatos na etapa de descoberta.",
            len(descoberta.candidatos),
        )

        pares = self.google_books.validar_candidatos_descoberta(descoberta.candidatos)

        validados = []
        for candidato, resultados_google in pares:
            validado = validate_book_match(candidato, resultados_google)

            if validado is None:
                logger.info(
                    "Candidato descartado (não confirmado no Google Books): %s — %s",
                    candidato.titulo,
                    candidato.autor,
                )
                continue

            validados.append(validado)

        logger.info(
            "%d de %d candidatos confirmados no Google Books.",
            len(validados),
            len(descoberta.candidatos),
        )

        vistos: set[str] = set()
        unicos = []
        for validado in validados:
            if validado.book.id in vistos:
                continue
            vistos.add(validado.book.id)
            unicos.append(validado)

        return unicos


    def _recomendar_via_llm(
        self,
        goal: UserGoal,
        idioma_resposta: str,
        ranking_candidates: list[RankingCandidate],
        candidatos_por_id: dict[str, BookCandidate],
    ) -> list[RecommendedBook]:
        """
        Avalia cada candidato numa chamada SEPARADA ao LLM (uma decisão
        booleana por vez), em vez de pedir N decisões independentes numa
        única resposta -- modelos pequenos (ex.: llama3.2:3b) seguem essa
        divisão com muito mais consistência.
        """

        scores_por_id = {
            candidate.id: candidate.score_deterministico for candidate in ranking_candidates
        }
        status_por_id = {
            candidate.id: candidate.status_validacao for candidate in ranking_candidates
        }

        aceitos: list[tuple[RankingCandidate, str]] = []

        for candidate in ranking_candidates:
            if len(aceitos) >= RECOMENDACOES_FINAIS:
                break

            system_prompt, user_prompt = build_single_candidate_prompt(
                objetivo_usuario=goal.objetivo,
                idioma_resposta=idioma_resposta,
                candidato=candidate,
            )

            try:
                raw_output = self.llm.chat_json(system_prompt, user_prompt)
                resultado = validate_single_candidate_output(raw_output)
            except (LlmOutputError, httpx.HTTPError) as exc:
                logger.warning(
                    "Avaliação individual falhou para '%s': %s. Tratando como não atende.",
                    candidate.titulo,
                    exc,
                )
                continue

            if not resultado.atende_objetivo:
                continue

            if any(
                self._titulos_parecidos(candidate.titulo, aceito.titulo)
                for aceito, _ in aceitos
            ):
                logger.info(
                    "Candidato '%s' descartado por ser edição/tradução de obra já aceita.",
                    candidate.titulo,
                )
                continue

            aceitos.append((candidate, resultado.justificativa))

        if not aceitos:
            raise LlmOutputError(
                "Nenhum candidato foi marcado como atende_objetivo=True pelo LLM."
            )

        logger.info(
            "%d candidatos com atende_objetivo=True (avaliação individual): %s",
            len(aceitos),
            [f"{c.titulo} — {c.autor}" for c, _ in aceitos],
        )

        return [
            RecommendedBook(
                id=candidate.id,
                titulo=candidate.titulo,
                autor=candidate.autor,
                thumbnail=candidatos_por_id[candidate.id].thumbnail,
                categorias=candidatos_por_id[candidate.id].categorias,
                average_rating=candidatos_por_id[candidate.id].average_rating,
                ratings_count=candidatos_por_id[candidate.id].ratings_count,
                posicao=posicao,
                score_deterministico=scores_por_id[candidate.id],
                justificativa=justificativa,
                status_validacao=status_por_id.get(candidate.id, "validado"),
            )
            for posicao, (candidate, justificativa) in enumerate(aceitos, start=1)
        ]

    @staticmethod
    def _titulos_parecidos(a: str, b: str) -> bool:
        """
        Compara dois títulos de forma tolerante, para evitar recomendar a
        mesma obra duas vezes (ex.: edições/traduções diferentes que o
        LLM aceitou em chamadas separadas, sem saber uma da outra).
        """
        ratio = SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
        return ratio >= 0.82


    @staticmethod
    def _fallback_por_score(
        top_candidatos: list[tuple[BookCandidate, float, str]],
    ) -> list[RecommendedBook]:

        melhores = top_candidatos[:RECOMENDACOES_FINAIS]

        return [
            RecommendedBook(
                id=candidate.id,
                titulo=candidate.titulo,
                autor=candidate.autor,
                thumbnail=candidate.thumbnail,
                categorias=candidate.categorias,
                average_rating=candidate.average_rating,
                ratings_count=candidate.ratings_count,
                posicao=posicao,
                score_deterministico=score,
                justificativa=(
                    "Selecionado automaticamente por score de "
                    f"compatibilidade com seu perfil ({motivo})."
                ),
            )
            for posicao, (candidate, score, motivo) in enumerate(melhores, start=1)
        ]


    def _recommend_legado(
        self,
        user: User,
        goal: UserGoal,
        preferencias: list[UserPreference],
        reading_history: list[ReadingHistory],
    ) -> RecommendationOut:

        termos_busca = self._extrair_termos_busca(goal.objetivo)

        logger.info("[legado] Termos utilizados na busca: %s", termos_busca)

        query = build_query_from_goal(
            objetivo=termos_busca,
            idioma_preferido=user.idioma_preferido,
            max_results=CANDIDATOS_DA_API,
        )

        candidatos_brutos = self.google_books.search(query)

        logger.info("[legado] Google Books retornou %d candidatos.", len(candidatos_brutos))

        candidatos_filtrados = filter_candidates(candidatos_brutos, reading_history)

        logger.info(
            "[legado] %d candidatos permaneceram após o filtro.",
            len(candidatos_filtrados),
        )

        if not candidatos_filtrados:
            raise NoBooksFoundError(
                "Nenhum livro novo encontrado para este objetivo "
                "(todos já foram lidos ou a busca não retornou resultados)."
            )

        pontuados = [
            (candidate, *score_candidate(candidate, user.idioma_preferido, preferencias))
            for candidate in candidatos_filtrados
        ]
        pontuados.sort(key=lambda item: item[1], reverse=True)

        top_candidatos = pontuados[:CANDIDATOS_PARA_LLM]

        candidatos_por_id: dict[str, BookCandidate] = {
            candidate.id: candidate for candidate, _, _ in top_candidatos
        }

        ranking_candidates = [
            RankingCandidate(
                id=candidate.id,
                titulo=candidate.titulo,
                autor=candidate.autor,
                idioma=candidate.idioma,
                paginas=candidate.paginas,
                categorias=candidate.categorias,
                descricao=candidate.descricao,
                score_deterministico=score,
                motivo_score=motivo,
            )
            for candidate, score, motivo in top_candidatos
        ]

        try:
            resultado_final = self._recomendar_via_llm(
                goal=goal,
                idioma_resposta=user.idioma_preferido or "pt",
                ranking_candidates=ranking_candidates,
                candidatos_por_id=candidatos_por_id,
            )
            fallback_usado = False
        except (LlmOutputError, httpx.HTTPError) as exc:
            logger.warning("[legado] LLM falhou. Usando fallback determinístico: %s", exc)
            resultado_final = self._fallback_por_score(top_candidatos)
            fallback_usado = True

        return RecommendationOut(
            objetivo=goal.objetivo,
            recomendacoes=resultado_final,
            fallback_usado=fallback_usado,
            pipeline="legado",
        )

    def _extrair_termos_busca(self, objetivo: str) -> str:
        try:
            system_prompt, user_prompt = build_keyword_extraction_prompt(objetivo)

            raw_output = self.llm.chat_json(system_prompt, user_prompt)

            resultado = validate_keyword_output(raw_output)

            termos = " ".join(
                keyword.strip() for keyword in resultado.keywords if keyword.strip()
            )

            if not termos:
                logger.warning(
                    "[legado] LLM não retornou palavras-chave. Usando objetivo original."
                )
                return objetivo

            logger.info("[legado] Palavras-chave extraídas: %s", termos)

            return termos

        except (KeywordExtractionError, httpx.HTTPError) as exc:
            logger.warning("[legado] Extração de palavras-chave falhou: %s", exc)
            return objetivo