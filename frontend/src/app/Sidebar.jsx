import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Inicio", icon: "bi-house-door-fill", end: true },
  { to: "/courses", label: "Cursos", icon: "bi-journal-bookmark-fill", roles: ["admin"] },
  { to: "/users", label: "Usuarios", icon: "bi-people-fill", roles: ["admin"] },
  {
    to: "/enrollments",
    label: "Inscripciones",
    icon: "bi-person-plus-fill",
    roles: ["admin", "teacher"],
  },
  { to: "/tasks", label: "Tareas", icon: "bi-journal-text", roles: ["teacher"] },
];

export default function Sidebar({ user }) {
  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(user?.role));

  return (
    <aside className="app-sidebar" aria-label="Navegación principal">
      {visibleItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `app-nav-link ${isActive ? "is-active" : ""}`.trim()}
        >
          <i className={`bi ${item.icon}`} aria-hidden="true" />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </aside>
  );
}
