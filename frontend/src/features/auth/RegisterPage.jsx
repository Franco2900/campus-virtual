import { useNavigate } from "react-router-dom";

import RegisterForm from "./RegisterForm.jsx";

export default function RegisterPage() {
  const navigate = useNavigate();
  return (
    <div className="auth-shell">
      <div className="campus-card auth-card">
        <div className="auth-brand">
          <span className="auth-brand__icon" aria-hidden="true">
            <i className="bi bi-person-plus-fill" />
          </span>
          <h1 className="h4 mb-0 brand-gradient">Crear cuenta</h1>
          <p className="text-secondary mb-0">Registrate para acceder al Campus Virtual</p>
        </div>
        <RegisterForm onSuccess={() => navigate("/login")} onShowLogin={() => navigate("/login")} />
      </div>
    </div>
  );
}
