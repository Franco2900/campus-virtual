export default function Spinner({ label = "Cargando...", className = "" }) {
  return (
    <div
      className={`d-flex align-items-center gap-2 text-secondary ${className}`.trim()}
      role="status"
    >
      <span className="spinner-border spinner-border-sm text-brand" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
