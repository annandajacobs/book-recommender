import { useEffect, useState } from "react";
import { api } from "../api/client";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState(null);
  const [genero, setGenero] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const data = await api.listPreferences();
    setPrefs(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!genero.trim()) return;
    setError(null);
    setSubmitting(true);
    try {
      await api.createPreference({ genero: genero.trim(), peso: 0.5 });
      setGenero("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function updateWeight(pref, peso) {
    setPrefs((prev) =>
      prev.map((p) => (p.id === pref.id ? { ...p, peso } : p))
    );
  }

  async function commitWeight(pref, peso) {
    await api.updatePreference(pref.id, { peso });
  }

  async function remove(pref) {
    await api.deletePreference(pref.id);
    await load();
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-eyebrow">Como você lê</div>
        <h1>Preferências de gênero</h1>
        <p>
          O peso indica o quanto cada gênero pesa no ranqueamento das suas
          recomendações — 0 quase ignora o gênero, 1 prioriza fortemente.
        </p>
      </div>

      {prefs === null ? (
        <Loader label="Carregando preferências…" />
      ) : prefs.length === 0 ? (
        <EmptyState
          title="Nenhuma preferência ainda"
          description="Adicione gêneros que você gosta para refinar suas recomendações."
        />
      ) : (
        <div className="section" style={{ marginBottom: 40 }}>
          <div className="form-panel" style={{ maxWidth: "100%" }}>
            {prefs.map((pref) => (
              <div className="pref-row" key={pref.id}>
                <span className="pref-genre">{pref.genero}</span>
                <div className="range-row">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={pref.peso}
                    onChange={(e) => updateWeight(pref, parseFloat(e.target.value))}
                    onMouseUp={(e) => commitWeight(pref, parseFloat(e.target.value))}
                    onTouchEnd={(e) => commitWeight(pref, parseFloat(e.target.value))}
                  />
                  <span className="range-value">{pref.peso.toFixed(2)}</span>
                </div>
                <button className="pref-remove" onClick={() => remove(pref)}>
                  remover
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="section-label">Novo gênero</div>
      <div className="form-panel">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleCreate}>
          <div className="field">
            <label htmlFor="genero">Gênero</label>
            <input
              id="genero"
              type="text"
              placeholder="Ex.: ficção científica, biografia, poesia"
              value={genero}
              onChange={(e) => setGenero(e.target.value)}
              required
            />
          </div>
          <button className="btn" type="submit" disabled={submitting}>
            {submitting ? "Salvando…" : "Adicionar gênero"}
          </button>
        </form>
      </div>
    </div>
  );
}
