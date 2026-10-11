export default function PageHeader({ title, subtitle, icon, actions }) {
  return (
    <header className="campus-page-header d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
      <div className="d-flex align-items-center gap-3">
        {icon && (
          <span className="auth-brand__icon" aria-hidden="true">
            <i className={`bi bi-${icon}`} />
          </span>
        )}
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="text-secondary mb-0">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="d-flex flex-wrap gap-2">{actions}</div>}
    </header>
  );
}
