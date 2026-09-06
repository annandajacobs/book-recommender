import { useState } from "react";

export default function BookCard({ book, onAddToHistory }) {
  const [added, setAdded] = useState(false);
  const [adding, setAdding] = useState(false);

  async function handleAdd() {
    setAdding(true);
    try {
      await onAddToHistory(book);
      setAdded(true);
    } finally {
      setAdding(false);
    }
  }

  const scorePercent = Math.round(book.score_deterministico * 100);

  return (
    <article className="book-card">
      {book.thumbnail ? (
        <img className="book-cover" src={book.thumbnail} alt="" />
      ) : (
        <div className="book-cover-fallback" aria-hidden="true">
          {book.titulo?.[0] ?? "?"}
        </div>
      )}

      <div className="book-main">
        <div className="book-top">
          <div>
            <div className="book-title">
              {book.posicao}. {book.titulo}
            </div>
            {book.autor && <div className="book-author">{book.autor}</div>}
          </div>
          <span className="book-score" title="Aderência calculada ao seu perfil">
            {scorePercent}
          </span>
        </div>

        {book.justificativa && (
          <p className="book-justificativa">{book.justificativa}</p>
        )}

        <div className="book-meta">
          {book.categorias?.slice(0, 3).map((c) => (
            <span className="book-tag" key={c}>
              {c}
            </span>
          ))}
          {book.average_rating != null && (
            <span className="book-rating">
              ★ {book.average_rating.toFixed(1)}
              {book.ratings_count ? ` (${book.ratings_count})` : ""}
            </span>
          )}
        </div>

        <div className="book-actions">
          {added ? (
            <span className="added">Adicionado ao histórico ✓</span>
          ) : (
            <button onClick={handleAdd} disabled={adding}>
              {adding ? "Adicionando…" : "Marcar como lendo"}
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
