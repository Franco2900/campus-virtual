export default function EmptyState({ icon = "bi-inbox", title, children }) {
  return (
    <div className="campus-empty">
      <i className={`bi ${icon}`} aria-hidden="true" />
      {title && <p className="fw-semibold mb-0">{title}</p>}
      {children && <p className="small mb-0">{children}</p>}
    </div>
  );
}
