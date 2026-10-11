import { Link } from "react-router-dom";

import { getRoleMeta } from "../ui/roles.js";
import ThemeToggle from "./ThemeToggle.jsx";

export default function Navbar({ user, onLogout }) {
  const meta = getRoleMeta(user?.role);

  return (
    <nav className="app-navbar">
      <div className="container-fluid d-flex align-items-center justify-content-between gap-3 py-2 px-3">
        <Link to="/" className="d-flex align-items-center gap-2">
          <span
            className="auth-brand__icon"
            style={{
              width: "2.25rem",
              height: "2.25rem",
              fontSize: "1.1rem",
              borderRadius: "0.7rem",
            }}
            aria-hidden="true"
          >
            <i className="bi bi-mortarboard-fill" />
          </span>
          <span className="fs-5 fw-bold brand-gradient">Campus Virtual</span>
        </Link>

        <div className="d-flex align-items-center gap-2">
          <ThemeToggle />
          {user && (
            <>
              <span
                className="role-chip d-none d-md-inline-flex"
                style={{ color: meta.color, background: meta.soft }}
              >
                <i className={`bi ${meta.icon}`} aria-hidden="true" />
                {user.first_name} · {meta.label}
              </span>
              <button
                type="button"
                className="btn btn-soft btn-sm d-inline-flex align-items-center gap-2"
                onClick={onLogout}
                data-testid="logout-button"
              >
                <i className="bi bi-box-arrow-right" aria-hidden="true" />
                <span className="d-none d-sm-inline">Cerrar sesión</span>
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
