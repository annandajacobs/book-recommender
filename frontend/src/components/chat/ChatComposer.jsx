const NIVEIS = [
  { value: "iniciante", label: "Iniciante" },
  { value: "intermediario", label: "Intermediário" },
  { value: "avancado", label: "Avançado" },
];

export default function ChatComposer({
  mode,
  onModeChange,
  text,
  onTextChange,
  nivel,
  onNivelChange,
  onSubmit,
  submitting,
  disabled,
  quickActions,
}) {
  const placeholder =
    mode === "genero"
      ? "Ex.: ficção científica, biografia, poesia…"
      : "O que você quer ler agora? Isso vira seu objetivo…";

  return (
    <div className="chat-composer">
      {quickActions && quickActions.length > 0 && (
        <div className="composer-actions">
          {quickActions.map((action) => (
            <button
              key={action.key}
              type="button"
              className="chip-action"
              onClick={action.onClick}
              disabled={disabled || action.disabled}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}

      <div className="composer-modes">
        <button
          type="button"
          className={"composer-mode-btn" + (mode === "objetivo" ? " active" : "")}
          onClick={() => onModeChange("objetivo")}
        >
          💭 Objetivo
        </button>
        <button
          type="button"
          className={"composer-mode-btn" + (mode === "genero" ? " active" : "")}
          onClick={() => onModeChange("genero")}
        >
          📚 Gênero
        </button>
      </div>

      {mode === "objetivo" && (
        <div className="nivel-pills">
          {NIVEIS.map((n) => (
            <button
              key={n.value}
              type="button"
              className={"nivel-pill" + (nivel === n.value ? " active" : "")}
              onClick={() => onNivelChange(n.value)}
            >
              {n.label}
            </button>
          ))}
        </div>
      )}

      <form
        className="composer-row"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <input
          type="text"
          value={text}
          placeholder={placeholder}
          onChange={(e) => onTextChange(e.target.value)}
          disabled={disabled || submitting}
        />
        <button className="btn" type="submit" disabled={disabled || submitting || !text.trim()}>
          {submitting ? "Enviando…" : "Enviar"}
        </button>
      </form>
    </div>
  );
}
