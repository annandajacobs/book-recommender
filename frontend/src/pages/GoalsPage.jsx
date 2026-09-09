import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

const NIVEL_LABELS = [
  { value: "iniciante", label: "Iniciante" },
  { value: "intermediario", label: "Intermediário" },
  { value: "avancado", label: "Avançado" },
];

export default function GoalsPage() {
  const navigate = useNavigate();
  const [goals, setGoals] = useState(null);
  const [error, setError] = useState(null);

  async function load() {
    try {
      const data = await api.listGoals(false);
      const sorted = [...data].sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
      setGoals(sorted);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function handleResume(goal) {
    navigate("/recomendacoes", { state: { resumeGoalId: goal.id } });
  }

  async function remove(goal) {
    await api.deleteGoal(goal.id);
    await load();
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-eyebrow">O que você já pediu</div>
        <h1>Meus pedidos</h1>
        <p>
          Todos os seus objetivos de leitura ficam registrados aqui. Retome qualquer um deles para buscar recomendações de novo - para pedir algo novo, é só acessar o chat novamente.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {goals === null ? (
        <Loader label="Carregando objetivos…" />
      ) : goals.length === 0 ? (
        <EmptyState
          title="Nenhum solicitação de recomendação de leitura ainda"
          description="Vá até o chat e conte o que você quer ler para começar."
        />
      ) : (
        <div className="goal-history-list">
          {goals.map((goal) => (
            <div className="goal-history-row" key={goal.id}>
              <div className="goal-history-main">
                <span className="goal-history-text">{goal.objetivo}</span>
                <div className="goal-history-meta">
                  <span>{NIVEL_LABELS.find(
                    (nivel) => nivel.value === goal.nivel_conhecimento
                  )?.label}</span>
                  <span>.</span>
                  <span>{new Date(goal.created_at).toLocaleDateString("pt-BR")}</span>
                </div>
              </div>
              <div className="goal-history-status">
                <span className={"goal-history-badge" + (goal.ativo ? "" : " is-inactive")}>
                  {goal.ativo ? "ativo" : "inativo"}
                </span>
              </div>
              <div className="goal-history-actions">
                <button className="btn-secondary btn" onClick={() => handleResume(goal)}>
                  Retomar e buscar recomendações
                </button>
                <button className="pref-remove" onClick={() => remove(goal)}>
                  remover
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
