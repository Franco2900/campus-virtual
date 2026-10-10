import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";

import { getMe, logout } from "./features/auth/api.js";
import LoginForm from "./features/auth/LoginForm.jsx";
import RegisterForm from "./features/auth/RegisterForm.jsx";
import CoursesPage from "./features/courses/CoursesPage.jsx";

const ROLE_LABELS = {
  student: "Estudiante",
  teacher: "Profesor",
  admin: "Administrador",
};

function LoginPage({ onSuccess }) {
  const navigate = useNavigate();
  return <LoginForm onSuccess={onSuccess} onShowRegister={() => navigate("/register")} />;
}

function RegisterPage() {
  const navigate = useNavigate();
  return (
    <RegisterForm onSuccess={() => navigate("/login")} onShowLogin={() => navigate("/login")} />
  );
}

function HomePage({ user, loading }) {
  if (loading) {
    return <p>Cargando...</p>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role === "admin") {
    return <Navigate to="/courses" replace />;
  }
  return <p>Bienvenido/a, {user.first_name}. Todavía no tenés secciones disponibles.</p>;
}

function ProtectedRoute({ user, loading, role, children }) {
  if (loading) {
    return <p>Cargando...</p>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (role && user.role !== role) {
    return <p role="alert">No tenés permisos para acceder a esta sección.</p>;
  }
  return children;
}

function AppRoutes({ user, loading, onLogin }) {
  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <LoginPage onSuccess={onLogin} />}
      />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <RegisterPage />} />
      <Route
        path="/courses"
        element={
          <ProtectedRoute user={user} loading={loading} role="admin">
            <CoursesPage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<HomePage user={user} loading={loading} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((currentUser) => setUser(currentUser))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // A failed logout request must not keep the logged-in view alive.
    } finally {
      setUser(null);
    }
  }

  return (
    <BrowserRouter>
      <main>
        <h1>Campus Virtual</h1>
        {user && (
          <header>
            <p>
              {user.first_name} {user.last_name} ({user.email}) —{" "}
              {ROLE_LABELS[user.role] ?? user.role}
            </p>
            <button type="button" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </header>
        )}
        <AppRoutes user={user} loading={loading} onLogin={setUser} />
      </main>
    </BrowserRouter>
  );
}
