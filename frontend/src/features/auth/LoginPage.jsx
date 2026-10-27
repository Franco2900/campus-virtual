import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import LoginForm from "./LoginForm.jsx";

export default function LoginPage({ onSuccess }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [registeredEmail, setRegisteredEmail] = useState(location.state?.registeredEmail ?? "");

  useEffect(() => {
    if (location.state?.registeredEmail) {
      navigate(location.pathname, { replace: true, state: null });
    }
  }, [location.pathname, location.state, navigate]);

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
        {registeredEmail && (
          <div className="alert alert-success py-2" role="status" data-testid="register-success">
            Cuenta creada. Ya podés iniciar sesión como {registeredEmail}.
          </div>
        )}
        <LoginForm
          onSuccess={onSuccess}
          onShowRegister={() => navigate("/register")}
          onSubmitStart={() => setRegisteredEmail("")}
        />
      </div>
    </div>
  );
}
