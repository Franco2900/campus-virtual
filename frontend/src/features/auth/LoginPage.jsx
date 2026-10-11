import { useNavigate } from "react-router-dom";

import LoginForm from "./LoginForm.jsx";

export default function LoginPage({ onSuccess }) {
  const navigate = useNavigate();

  return (
    <div className="auth-shell">
      <div className="campus-card auth-card">
        <div className="auth-brand">
          <span className="auth-brand__icon" aria-hidden="true">
            <i className="bi bi-mortarboard-fill" />
          </span>
          <h1 className="h4 mb-0 brand-gradient">Campus Virtual</h1>
          <p className="text-secondary mb-0">Plataforma de gestión académica</p>
        </div>
        <LoginForm onSuccess={onSuccess} onShowRegister={() => navigate("/register")} />
      </div>
    </div>
  );
}
