export default function Loader({ label = "Carregando…" }) {
  return (
    <div className="loader">
      <span className="loader-mark" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
