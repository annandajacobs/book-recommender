import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import BookCard from "../components/BookCard";
import EmptyState from "../components/EmptyState";
import {
  SystemBubble,
  SystemContent,
  TypingBubble,
  UserBubble,
} from "../components/chat/MessageBubble";
import ChatComposer from "../components/chat/ChatComposer";

const NIVEL_LABELS = {
  iniciante: "iniciante",
  intermediario: "intermediário",
  avancado: "avançado",
};

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function RecommendationsPage() {
  const navigate = useNavigate();
  const [thread, setThread] = useState([]);
  const [goals, setGoals] = useState([]);
  const [prefs, setPrefs] = useState([]);
  const [goalId, setGoalId] = useState(null);
  const [step, setStep] = useState("loading"); // loading | ask_goal | ready
  const [mode, setMode] = useState("objetivo");
  const [text, setText] = useState("");
  const [nivel, setNivel] = useState("iniciante");
  const [submitting, setSubmitting] = useState(false);

  const endRef = useRef(null);
  const initialized = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [thread]);

  function push(msg) {
    const id = uid();
    setThread((prev) => [...prev, { id, ...msg }]);
    return id;
  }

  function resolve(id, msg) {
    setThread((prev) => prev.map((m) => (m.id === id ? { ...m, ...msg, id } : m)));
  }

  async function runRecommendations(gid) {
    const typingId = push({ role: "system", kind: "typing", label: "Buscando recomendações…" });
    try {
      const data = await api.getRecommendations(gid);
      resolve(typingId, { role: "system", kind: "books", payload: data });
    } catch (err) {
      resolve(typingId, { role: "system", kind: "error", text: err.message });
    }
  }

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    (async () => {
      push({
        role: "system",
        kind: "text",
        text: "Oi! Vamos achar sua próxima leitura. 📚",
      });

      let goalsData = [];
      let prefsData = [];
      try {
        [goalsData, prefsData] = await Promise.all([
          api.listGoals(true),
          api.listPreferences(),
        ]);
      } catch (err) {
        push({ role: "system", kind: "error", text: err.message });
        return;
      }

      setGoals(goalsData);
      setPrefs(prefsData);

      if (goalsData.length === 0) {
        push({
          role: "system",
          kind: "text",
          text: "Você ainda não tem um objetivo de leitura. Me conta o que você quer ler agora — pode ser um tema, uma habilidade ou só um gênero.",
        });
        setMode("objetivo");
        setStep("ask_goal");
        return;
      }

      const active = goalsData.find((g) => g.ativo) ?? goalsData[0];
      setGoalId(active.id);

      push({
        role: "system",
        kind: "context",
        payload: { goal: active, prefs: prefsData },
      });

      push({
        role: "system",
        kind: "text",
        text: "Quer manter esse objetivo ou me contar outra coisa? Quando estiver pronto, toque em \"Buscar de novo\" ou digite um novo objetivo.",
      });

      setMode("objetivo");
      setStep("ready");
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreateGoal(objetivo) {
    push({ role: "user", kind: "text", text: objetivo });
    setSubmitting(true);
    try {
      const toDeactivate = goals.filter((g) => g.ativo);
      for (const g of toDeactivate) {
        await api.updateGoal(g.id, { ativo: false });
      }
      const newGoal = await api.createGoal({
        objetivo: objetivo.trim(),
        nivel_conhecimento: nivel,
      });
      setGoals((prev) => [...prev.map((g) => ({ ...g, ativo: false })), newGoal]);
      setGoalId(newGoal.id);
      setText("");

      push({
        role: "system",
        kind: "text",
        text: `Anotado — "${objetivo.trim()}" (nível ${NIVEL_LABELS[nivel]}).`,
      });

      await runRecommendations(newGoal.id);

      if (step === "ask_goal" && prefs.length === 0) {
        push({
          role: "system",
          kind: "text",
          text: "Se quiser, me conta um gênero que você curte — é opcional, só ajuda a refinar.",
        });
        setMode("genero");
      }
      setStep("ready");
    } catch (err) {
      push({ role: "system", kind: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreatePreference(genero) {
    push({ role: "user", kind: "text", text: `Gosto de ${genero}` });
    setSubmitting(true);
    try {
      const newPref = await api.createPreference({ genero: genero.trim(), peso: 0.6 });
      setPrefs((prev) => [...prev, newPref]);
      setText("");
      push({
        role: "system",
        kind: "text",
        text: `Beleza, vou considerar mais livros de ${genero.trim()} a partir de agora.`,
      });
      if (goalId) await runRecommendations(goalId);
    } catch (err) {
      push({ role: "system", kind: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit() {
    if (!text.trim() || submitting) return;
    if (mode === "genero") handleCreatePreference(text);
    else handleCreateGoal(text);
  }

  async function handleRefetch() {
    if (!goalId) return;
    push({ role: "user", kind: "action", text: "🔄 Buscar recomendações de novo" });
    await runRecommendations(goalId);
  }

  async function handleAddToHistory(book) {
    await api.createHistoryEntry({
      book_id: book.id,
      titulo: book.titulo,
      autor: book.autor,
      status: "lendo",
    });
    push({
      role: "system",
      kind: "text",
      text: `Marquei "${book.titulo}" como lendo. Dá pra ajustar o status no Histórico.`,
    });
  }

  const quickActions =
    step === "ready"
      ? [
          { key: "refetch", label: "🔄 Buscar de novo", onClick: handleRefetch },
          { key: "historico", label: "📖 Ver histórico", onClick: () => navigate("/historico") },
        ]
      : [];

  return (
    <div className="chat-page">
      <div className="chat-page-header">
        <div className="page-eyebrow">Para você</div>
        <h1>Conversa</h1>
      </div>

      <div className="chat-thread">
        {thread.map((msg) => {
          if (msg.kind === "typing") {
            return <TypingBubble key={msg.id} label={msg.label} />;
          }
          if (msg.role === "user") {
            return <UserBubble key={msg.id}>{msg.text}</UserBubble>;
          }
          if (msg.kind === "error") {
            return (
              <SystemBubble key={msg.id}>
                <span className="msg-error">{msg.text}</span>
              </SystemBubble>
            );
          }
          if (msg.kind === "context") {
            const { goal, prefs: p } = msg.payload;
            return (
              <SystemContent key={msg.id} label="Contexto atual">
                <div className="context-chips">
                  <span className="goal-chip is-active">
                    <span>{goal.objetivo}</span>
                    <span className="level">{goal.nivel_conhecimento}</span>
                  </span>
                  {p.map((pref) => (
                    <span className="goal-chip" key={pref.id}>
                      {pref.genero}
                    </span>
                  ))}
                </div>
              </SystemContent>
            );
          }
          if (msg.kind === "books") {
            const result = msg.payload;
            return (
              <SystemContent key={msg.id} label="Recomendações">
                <div className="pipeline-note">
                  <span
                    className={"pipeline-dot" + (result.fallback_usado ? " fallback" : "")}
                  />
                  {result.fallback_usado
                    ? "Usando busca por palavras-chave (a descoberta semântica não retornou resultados)."
                    : "Descoberta semântica via modelo de linguagem, validada no Google Books."}
                </div>
                {result.recomendacoes.length === 0 ? (
                  <EmptyState
                    title="Nada encontrado para esse objetivo"
                    description="Tente ajustar o texto do objetivo ou adicionar preferências de gênero."
                  />
                ) : (
                  <div className="book-list">
                    {result.recomendacoes.map((book) => (
                      <BookCard key={book.id} book={book} onAddToHistory={handleAddToHistory} />
                    ))}
                  </div>
                )}
              </SystemContent>
            );
          }
          // text (system or fallback)
          return <SystemBubble key={msg.id}>{msg.text}</SystemBubble>;
        })}
        <div ref={endRef} />
      </div>

      <ChatComposer
        mode={mode}
        onModeChange={setMode}
        text={text}
        onTextChange={setText}
        nivel={nivel}
        onNivelChange={setNivel}
        onSubmit={handleSubmit}
        submitting={submitting}
        disabled={step === "loading"}
        quickActions={quickActions}
      />
    </div>
  );
}
