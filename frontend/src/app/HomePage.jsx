import { Card, PageHeader, RoleBadge } from "../ui/index.js";
import { getRoleMeta } from "../ui/roles.js";

export default function HomePage({ user }) {
  const meta = getRoleMeta(user.role);

  return (
    <div>
      <PageHeader
        title={`Hola, ${user.first_name}`}
        subtitle="Bienvenido/a al Campus Virtual"
        icon="bi-house-door-fill"
      />

      <div className="row g-3">
        <div className="col-12 col-md-6 col-xl-4">
          <Card className="campus-stat h-100">
            <span className="campus-stat__icon bg-brand-soft" aria-hidden="true">
              <i className="bi bi-person-badge-fill" />
            </span>
            <div>
              <div className="campus-stat__value">{user.first_name}</div>
              <div className="campus-stat__label">Tu cuenta</div>
            </div>
          </Card>
        </div>

        <div className="col-12 col-md-6 col-xl-4">
          <Card className="campus-stat h-100">
            <span
              className="campus-stat__icon"
              style={{ color: meta.color, background: meta.soft }}
              aria-hidden="true"
            >
              <i className={`bi ${meta.icon}`} />
            </span>
            <div>
              <RoleBadge role={user.role} />
              <div className="campus-stat__label mt-1">Rol asignado</div>
            </div>
          </Card>
        </div>
      </div>

      <Card className="p-4 mt-3">
        <div className="d-flex align-items-center gap-2 mb-2">
          <i className="bi bi-info-circle-fill text-brand" aria-hidden="true" />
          <span className="fw-semibold">Próximamente</span>
        </div>
        <p className="text-secondary mb-0">
          Todavía no hay secciones disponibles para tu rol. Cuando se habiliten los cursos, tareas y
          calificaciones, vas a poder verlas desde acá.
        </p>
      </Card>
    </div>
  );
}
