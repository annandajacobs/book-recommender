# ruff: noqa: ISC004, BLE001
"""Mede as métricas "objetivas" do recomendador (Grupo 1), rodando o
pipeline de verdade contra um pequeno conjunto de objetivos de exemplo.

Isso NÃO é um teste de pytest e não deve rodar em CI: usa o LLM e o Google
Books reais, não é determinístico, tem custo por execução e ESCREVE no
banco configurado em `settings.database_url` (cria e depois apaga um
usuário/objetivo fake por execução). É pra ser rodado manualmente sempre
que você quiser gerar uma nova evidência de qualidade (por exemplo, depois
de mudar um prompt), e o resultado fica salvo em `evals/results/` para
consulta futura — inclusive linkado no README.

ATENÇÃO — banco de dados:
    Este script usa `api.database.session.SessionLocal`, ou seja, aponta
    pra o MESMO banco que a aplicação usaria (`settings.database_url`).
    Rode com `DATABASE_URL` apontando para um banco de teste/eval, nunca
    para produção. Como salvaguarda mínima, o script exige a flag
    `--eu-sei-que-isso-usa-o-banco-configurado` para seguir em frente.

Uso:
    uv run python evals/run_group1_metrics.py --eu-sei-que-isso-usa-o-banco-configurado
    uv run python evals/run_group1_metrics.py --runs 5 --out evals/results/group1_2026-09-10.md \
        --eu-sei-que-isso-usa-o-banco-configurado

Métricas cobertas (ver README > "Qualidade do recomendador"):
    - completude: recomendações geradas / RECOMENDACOES_FINAIS (3)
      (ver nota abaixo — isto substitui a antiga ideia de "% de livros
      válidos / total_candidatos", que não existe como número exposto
      pelo service hoje)
    - taxa de fallback (fallback_usado)
    - taxa de uso do pipeline "descoberta" vs "legado"
    - taxa de recomendações finais com status_validacao="incerto"
      (livro aceito pelo _descobrir_e_validar com confiança mais baixa,
      mesmo sem cair em fallback — ver MatchStatus em book_validator.py)
    - tempo médio (p50 / p95) por execução
    - custo médio por recomendação: **n/d** (ver nota sobre tokens abaixo)

NOTA sobre a métrica "% de livros válidos":
    O `RecommendationOut` real (api.schemas.recommendation) só expõe
    `objetivo`, `recomendacoes`, `fallback_usado` e `pipeline` — não expõe
    quantos candidatos vieram do Google Books nem quantos sobreviveram aos
    filtros internos (`_descobrir_e_validar`, `filter_candidates`, etc. são
    passos internos de `RecommendationService.recommend()`). Por isso, a
    métrica calculada aqui é "completude": quantas das `RECOMENDACOES_FINAIS`
    vagas o pipeline conseguiu preencher (`len(recomendacoes) / 3`). Isso
    NÃO é a mesma coisa que "% de candidatos aprovados pelo LLM/Google
    Books" — se quiser essa métrica mais fina, é preciso o
    `RecommendationService` expor essas contagens intermediárias (por
    exemplo devolvendo-as no `RecommendationOut` como campos de
    diagnóstico, ou emitindo-as via logging estruturado que este script
    possa capturar).

NOTA sobre custo/tokens:
    `LlmClient.chat_json()` (api.infrastructure.llm.client) hoje só
    retorna `data["message"]["content"]` e descarta o resto da resposta
    do Ollama — mas o Ollama normalmente devolve `prompt_eval_count` e
    `eval_count` no JSON completo. Para medir custo de verdade seria
    necessário instrumentar o client para capturar e expor esses campos
    (ex.: um atributo tipo `self.last_usage` setado a cada chamada, ou
    o método retornando uma tupla (texto, usage)). Não fiz essa mudança
    aqui por não ser um script de teste o lugar de alterar código de
    produção sem combinar — o campo de custo fica "n/d" até isso ser
    decidido e implementado.
"""

from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from api.database.session import SessionLocal
from api.infrastructure.google_books.book_validator import MatchStatus
from api.models.user import User
from api.models.user_goal import NivelConhecimento, UserGoal
from api.services.recommendation_service import (
    RECOMENDACOES_FINAIS,
    RecommendationService,
)

PRECO_USD_POR_1M_TOKENS_ENTRADA: float | None = None
PRECO_USD_POR_1M_TOKENS_SAIDA: float | None = None

OBJETIVOS_EXEMPLO: list[dict] = [
    {"objetivo": "aprender python do zero", "nivel_conhecimento": "iniciante"},
    {"objetivo": "aprofundar em arquitetura de software", "nivel_conhecimento": "avancado"},
    {"objetivo": "ler um romance envolvente", "nivel_conhecimento": "iniciante"},
    {"objetivo": "história de amor clássica com inimigos-a-amantes", "nivel_conhecimento": "iniciante"},
    {"objetivo": "biografia de um cientista", "nivel_conhecimento": "intermediario"},
    {"objetivo": "livro de poesia contemporânea brasileira", "nivel_conhecimento": "iniciante"},
    {"objetivo": "entender economia comportamental", "nivel_conhecimento": "intermediario"},
    {"objetivo": "xn7q##ruído_proposital_sem_sentido##", "nivel_conhecimento": "iniciante"},
]


@dataclass
class RunResult:
    objetivo: str
    recomendacoes_geradas: int
    recomendacoes_incertas: int
    fallback_usado: bool
    pipeline: str | None
    tempo_total_ms: float
    tokens_entrada: int | None = None
    tokens_saida: int | None = None
    erro: str | None = None

    @property
    def completude(self) -> float | None:
        """Fração das RECOMENDACOES_FINAIS vagas que foram preenchidas.

        Não é "% de candidatos válidos" (essa contagem intermediária não
        é exposta pelo service hoje — ver NOTA no docstring do módulo).
        """
        if self.erro is not None:
            return None
        return self.recomendacoes_geradas / RECOMENDACOES_FINAIS

    @property
    def custo_usd(self) -> float | None:
        if (
            self.tokens_entrada is None
            or self.tokens_saida is None
            or PRECO_USD_POR_1M_TOKENS_ENTRADA is None
            or PRECO_USD_POR_1M_TOKENS_SAIDA is None
        ):
            return None
        return (
            self.tokens_entrada / 1_000_000 * PRECO_USD_POR_1M_TOKENS_ENTRADA
            + self.tokens_saida / 1_000_000 * PRECO_USD_POR_1M_TOKENS_SAIDA
        )


@dataclass
class Report:
    timestamp: str
    commit: str
    runs_por_objetivo: int
    resultados: list[RunResult] = field(default_factory=list)

    def to_markdown(self) -> str:
        ok = [r for r in self.resultados if r.erro is None]
        erros = [r for r in self.resultados if r.erro is not None]

        completudes = [r.completude for r in ok if r.completude is not None]
        tempos = [r.tempo_total_ms for r in ok]
        custos = [r.custo_usd for r in ok if r.custo_usd is not None]
        taxa_fallback = sum(1 for r in ok if r.fallback_usado) / len(ok) if ok else None
        taxa_legado = (
            sum(1 for r in ok if r.pipeline == "legado") / len(ok) if ok else None
        )
        total_recomendacoes = sum(r.recomendacoes_geradas for r in ok)
        total_incertas = sum(r.recomendacoes_incertas for r in ok)
        taxa_incertas = (
            total_incertas / total_recomendacoes if total_recomendacoes else None
        )

        def fmt_pct(v: float | None) -> str:
            return f"{v * 100:.1f}%" if v is not None else "n/d"

        def fmt_ms(v: float | None) -> str:
            return f"{v:.0f} ms" if v is not None else "n/d"

        def fmt_usd(v: float | None) -> str:
            return f"US$ {v:.4f}" if v is not None else "n/d"

        def pctl(data: list[float], p: float) -> float | None:
            if not data:
                return None
            s = sorted(data)
            k = round((len(s) - 1) * p)
            return s[k]

        linhas = [
            "# Relatório de métricas — Grupo 1 (objetivas)",
            "",
            f"- **Data:** {self.timestamp}",
            f"- **Commit:** `{self.commit}`",
            f"- **Execuções por objetivo:** {self.runs_por_objetivo}",
            f"- **Objetivos testados:** {len(OBJETIVOS_EXEMPLO)}",
            f"- **Execuções com erro:** {len(erros)} / {len(self.resultados)}",
            "",
            "## Resumo agregado",
            "",
            "| Métrica | Valor |",
            "|---|---|",
            f"| Completude (recomendações geradas / {RECOMENDACOES_FINAIS}) | "
            f"{fmt_pct(statistics.mean(completudes)) if completudes else 'n/d'} |",
            f"| Taxa de fallback | {fmt_pct(taxa_fallback)} |",
            f"| Taxa de uso do pipeline legado | {fmt_pct(taxa_legado)} |",
            f"| Recomendações finais com status 'incerto' | "
            f"{fmt_pct(taxa_incertas)} ({total_incertas}/{total_recomendacoes}) |",
            f"| Tempo total — p50 | {fmt_ms(pctl(tempos, 0.5))} |",
            f"| Tempo total — p95 | {fmt_ms(pctl(tempos, 0.95))} |",
            f"| Custo médio por recomendação | "
            f"{fmt_usd(statistics.mean(custos)) if custos else 'n/d (tokens não instrumentados)'} |",
            "",
            "## Por objetivo",
            "",
            "| Objetivo | Completude | Pipeline | Fallback | Incertos | Tempo (ms) | Custo |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in self.resultados:
            if r.erro:
                linhas.append(f"| {r.objetivo} | — | — | — | — | — | **erro:** {r.erro} |")
                continue
            linhas.append(
                f"| {r.objetivo} | {fmt_pct(r.completude)} | {r.pipeline} | "
                f"{'sim' if r.fallback_usado else 'não'} | "
                f"{r.recomendacoes_incertas}/{r.recomendacoes_geradas} | "
                f"{r.tempo_total_ms:.0f} | {fmt_usd(r.custo_usd)} |"
            )

        linhas += [
            "",
            "---",
            "_Gerado por `evals/run_group1_metrics.py`. 'Completude' mede quantas",
            "das vagas de recomendação foram preenchidas, não a taxa de aprovação",
            "de candidatos internos (essa contagem não é exposta pelo service hoje).",
            "Custo fica 'n/d' até o LlmClient expor uso de tokens. Não substitui uma",
            "medição real, que deve ser rodada e versionada aqui sempre que o",
            "pipeline (prompt, filtros, ranking) mudar de forma relevante._",
        ]
        return "\n".join(linhas)


def get_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "desconhecido"


def _criar_usuario_e_objetivo_teste(db, objetivo_dict: dict) -> tuple[User, UserGoal]:
    """Cria um usuário e um objetivo fake no banco configurado, só para
    esta execução do eval. Quem chama é responsável por apagar o usuário
    depois (cascade cuida do goal/preferences/reading_history).
    """
    sufixo = uuid.uuid4().hex[:12]
    user = User(
        nome="Eval Bot",
        email=f"eval-group1-{sufixo}@example.invalid",
        senha_hash="eval-fake-hash-nao-usado-para-login",
        idioma_preferido="pt",
    )
    db.add(user)
    db.flush()

    goal = UserGoal(
        user_id=user.id,
        objetivo=objetivo_dict["objetivo"],
        nivel_conhecimento=NivelConhecimento(objetivo_dict["nivel_conhecimento"]),
    )
    db.add(goal)
    db.commit()
    db.refresh(user)
    db.refresh(goal)
    return user, goal


def run_one(objetivo_dict: dict) -> RunResult:
    """Roda o pipeline real (RecommendationService.recommend) para um
    objetivo, usando um usuário/objetivo fake criado só para este teste.
    """
    db = SessionLocal()
    user: User | None = None
    t0 = time.perf_counter()

    try:
        user, goal = _criar_usuario_e_objetivo_teste(db, objetivo_dict)

        service = RecommendationService(db)
        resultado = service.recommend(user, goal)

        tempo_total_ms = (time.perf_counter() - t0) * 1000

        incertas = sum(
            1
            for livro in resultado.recomendacoes
            if livro.status_validacao == MatchStatus.INCERTO.value
        )

        return RunResult(
            objetivo=objetivo_dict["objetivo"],
            recomendacoes_geradas=len(resultado.recomendacoes),
            recomendacoes_incertas=incertas,
            fallback_usado=resultado.fallback_usado,
            pipeline=resultado.pipeline,
            tempo_total_ms=tempo_total_ms,
        )
    except Exception as exc:
        tempo_total_ms = (time.perf_counter() - t0) * 1000
        return RunResult(
            objetivo=objetivo_dict["objetivo"],
            recomendacoes_geradas=0,
            recomendacoes_incertas=0,
            fallback_usado=False,
            pipeline=None,
            tempo_total_ms=tempo_total_ms,
            erro=str(exc),
        )
    finally:
        try:
            if user is not None:
                db.delete(user)
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", type=int, default=3, help="execuções por objetivo (reduz ruído do LLM)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="caminho do relatório de saída (default: evals/results/group1_<data>.md)",
    )
    parser.add_argument(
        "--eu-sei-que-isso-usa-o-banco-configurado",
        action="store_true",
        dest="confirma_banco",
        help=(
            "obrigatório: confirma que você sabe que este script escreve "
            "(e depois apaga) um usuário/objetivo fake no banco apontado "
            "por DATABASE_URL/settings.database_url. Aponte isso para um "
            "banco de teste/eval, não para produção."
        ),
    )
    args = parser.parse_args()

    if not args.confirma_banco:
        print(
            "Recusando rodar sem --eu-sei-que-isso-usa-o-banco-configurado.\n"
            "Este script escreve no banco configurado em settings.database_url "
            "(cria e apaga um usuário fake por execução). Confirme que isso "
            "aponta para um banco de teste/eval antes de rodar.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    report = Report(timestamp=timestamp, commit=get_commit_hash(), runs_por_objetivo=args.runs)

    for objetivo in OBJETIVOS_EXEMPLO:
        for _ in range(args.runs):
            report.resultados.append(run_one(objetivo))

    out_path = Path(
        args.out or f"evals/results/group1_{datetime.now(UTC).strftime('%Y-%m-%d')}.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report.to_markdown(), encoding="utf-8")
    print(f"Relatório salvo em {out_path}")


if __name__ == "__main__":
    main()