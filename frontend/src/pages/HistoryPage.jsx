import { useEffect, useState } from "react";
import { api } from "../api/client";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

const STATUS_LABELS = {
  lendo: "Lendo",
  concluido: "Concluído",
  abandonado: "Abandonado",
};

const FEEDBACK_OPTIONS = [
  { value: "gostou", icon: "👍", label: "Gostou" },
  { value: "neutro", icon: "😐", label: "Neutro" },
  { value: "nao_gostou", icon: "👎", label: "Não gostou" },
];

export default function HistoryPage() {
  const [entries, setEntries] = useState(null);

  async function load() {
    const data = await api.listHistory();
    setEntries(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function updateStatus(entry, status) {
    setEntries((prev) =>
      prev.map((e) => (e.id === entry.id ? { ...e, status } : e))
    );
    await api.updateHistoryEntry(entry.id, { status });
  }

  async function updateFeedback(entry, feedback) {
    const next = entry.feedback === feedback ? null : feedback;
    setEntries((prev) =>
      prev.map((e) => (e.id === entry.id ? { ...e, feedback: next } : e))
    );
    await api.updateHistoryEntry(entry.id, { feedback: next });
  }

  async function remove(entry) {
    await api.deleteHistoryEntry(entry.id);
    await load();
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-eyebrow">Sua estante</div>
        <h1>Histórico de leitura</h1>
        <p>Livros que você marcou a partir de recomendações, com status e feedback.</p>
      </div>

      {entries === null ? (
        <Loader label="Carregando histórico…" />
      ) : entries.length === 0 ? (
        <EmptyState
          title="Nenhum livro no histórico ainda"
          description="Marque um livro como 'lendo' a partir da página de recomendações para começar."
        />
      ) : (
        <div className="history-list">
          {entries.map((entry) => (
            <div className="history-row" key={entry.id}>
              <div className="history-title">
                <div className="t">{entry.titulo}</div>
                {entry.autor && <div className="a">{entry.autor}</div>}
              </div>

              <select
                className="status-select"
                value={entry.status}
                onChange={(e) => updateStatus(entry, e.target.value)}
              >
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>

              <div className="feedback-buttons">
                {FEEDBACK_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    className={
                      "feedback-btn" +
                      (entry.feedback === opt.value ? " selected" : "")
                    }
                    title={opt.label}
                    onClick={() => updateFeedback(entry, opt.value)}
                  >
                    {opt.icon}
                  </button>
                ))}
              </div>

              <button className="pref-remove" onClick={() => remove(entry)}>
                remover
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
