import { useEffect, useState } from "react";
import { api } from "../api/client";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

const NIVEIS = [
  { value: "iniciante", label: "Iniciante" },
  { value: "intermediario", label: "Intermediário" },
  { value: "avancado", label: "Avançado" },
];

export default function GoalsPage() {
  const [goals, setGoals] = useState(null);
  const [objetivo, setObjetivo] = useState("");
  const [nivel, setNivel] = useState("iniciante");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const data = await api.listGoals(false);
    setGoals(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!objetivo.trim()) return;
    setError(null);
    setSubmitting(true);
    try {
      await api.createGoal({ objetivo: objetivo.trim(), nivel_conhecimento: nivel });
      setObjetivo("");
      setNivel("iniciante");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleActive(goal) {
    await api.updateGoal(goal.id, { ativo: !goal.ativo });
    await load();
  }

  async function remove(goal) {
    await api.deleteGoal(goal.id);
    await load();
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-eyebrow">O que você quer ler</div>
        <h1>Objetivos de leitura</h1>
        <p>
          Um objetivo guia a recomendação — pode ser um tema para estudar,
          uma habilidade a desenvolver, ou simplesmente um gênero que você
          quer explorar agora.
        </p>
      </div>

      {goals === null ? (
        <Loader label="Carregando objetivos…" />
      ) : goals.length === 0 ? (
        <EmptyState
          title="Nenhum objetivo ainda"
          description="Crie o primeiro objetivo abaixo para começar a receber recomendações."
        />
      ) : (
        <div className="chip-row">
          {goals.map((goal) => (
            <span
              key={goal.id}
              className={"goal-chip" + (goal.ativo ? " is-active" : "")}
            >
              <span>{goal.objetivo}</span>
              <span className="level">{goal.nivel_conhecimento}</span>
              <button
                onClick={() => toggleActive(goal)}
                title={goal.ativo ? "Desativar" : "Ativar"}
                style={{ fontSize: 11, textDecoration: "underline" }}
              >
                {goal.ativo ? "ativo" : "inativo"}
              </button>
              <button onClick={() => remove(goal)} title="Remover" aria-label="Remover">
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="section-label">Novo objetivo</div>
      <div className="form-panel">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleCreate}>
          <div className="field">
            <label htmlFor="objetivo">Objetivo</label>
            <input
              id="objetivo"
              type="text"
              placeholder="Ex.: aprender python, filosofia estoica, ficção distópica"
              value={objetivo}
              onChange={(e) => setObjetivo(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="nivel">Nível de conhecimento</label>
            <select id="nivel" value={nivel} onChange={(e) => setNivel(e.target.value)}>
              {NIVEIS.map((n) => (
                <option key={n.value} value={n.value}>
                  {n.label}
                </option>
              ))}
            </select>
          </div>
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "Salvando…" : "Adicionar objetivo"}
          </button>
        </form>
      </div>
    </div>
  );
}
