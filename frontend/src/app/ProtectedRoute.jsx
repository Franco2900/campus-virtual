import { Navigate, useLocation } from "react-router-dom";

import { Spinner } from "../ui/index.js";

export default function ProtectedRoute({ user, loading, role, children }) {
  const location = useLocation();

  if (loading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <Spinner label="Cargando sesión..." />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (role && user.role !== role) {
    return (
      <div className="campus-card p-4 d-flex align-items-center gap-3" role="alert">
        <i className="bi bi-shield-slash fs-3 text-role-admin" aria-hidden="true" />
        <div>
          <div className="fw-semibold">Acceso restringido</div>
          <div className="text-secondary">No tenés permisos para acceder a esta sección.</div>
        </div>
      </div>
    );
  }

  return children;
}
