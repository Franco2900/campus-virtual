import { useEffect, useState } from "react";

import { getMe, logout } from "./features/auth/api.js";
import LoginForm from "./features/auth/LoginForm.jsx";
import RegisterForm from "./features/auth/RegisterForm.jsx";

const ROLE_LABELS = {
  student: "Estudiante",
  teacher: "Profesor",
  admin: "Administrador",
};

export default function App() {
  const [user, setUser] = useState(null);
  const [showLogin, setShowLogin] = useState(true);

  useEffect(() => {
    getMe()
      .then((currentUser) => setUser(currentUser))
      .catch(() => setUser(null));
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // A failed logout request must not keep the logged-in view alive.
    } finally {
      setUser(null);
      setShowLogin(true);
    }
  }

  return (
    <main>
      <h1>Campus Virtual</h1>
      {user ? (
        <header>
          <p>
            {user.first_name} {user.last_name} ({user.email}) —{" "}
            {ROLE_LABELS[user.role] ?? user.role}
          </p>
          <button type="button" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </header>
      ) : showLogin ? (
        <LoginForm onSuccess={setUser} onShowRegister={() => setShowLogin(false)} />
      ) : (
        <RegisterForm onSuccess={() => setShowLogin(true)} onShowLogin={() => setShowLogin(true)} />
      )}
    </main>
  );
}
