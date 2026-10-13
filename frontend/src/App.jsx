import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./app/AppLayout.jsx";
import HomePage from "./app/HomePage.jsx";
import ProtectedRoute from "./app/ProtectedRoute.jsx";
import { getMe, logout } from "./features/auth/api.js";
import LoginPage from "./features/auth/LoginPage.jsx";
import RegisterPage from "./features/auth/RegisterPage.jsx";
import CoursesPage from "./features/courses/CoursesPage.jsx";
import EnrollmentsPage from "./features/enrollments/EnrollmentsPage.jsx";
import SubmissionsPage from "./features/submissions/SubmissionsPage.jsx";
import TasksPage from "./features/tasks/TasksPage.jsx";
import UsersPage from "./features/users/UsersPage.jsx";
import { ThemeProvider } from "./theme/ThemeProvider.jsx";
import { ToastProvider } from "./ui/index.js";

function HomeRoute({ user }) {
  if (user.role === "admin") {
    return <Navigate to="/courses" replace />;
  }
  return <HomePage user={user} />;
}

function AppRoutes({ user, loading, onLogin, onLogout }) {
  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <LoginPage onSuccess={onLogin} />}
      />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <RegisterPage />} />

      <Route
        element={
          <ProtectedRoute user={user} loading={loading}>
            <AppLayout user={user} onLogout={onLogout} />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<HomeRoute user={user} />} />
        <Route
          path="/courses"
          element={
            <ProtectedRoute user={user} loading={loading} role="admin">
              <CoursesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute user={user} loading={loading} role="admin">
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/enrollments"
          element={
            <ProtectedRoute user={user} loading={loading} roles={["admin", "teacher"]}>
              <EnrollmentsPage user={user} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tasks"
          element={
            <ProtectedRoute user={user} loading={loading} role="teacher">
              <TasksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/submissions"
          element={
            <ProtectedRoute user={user} loading={loading} role="student">
              <SubmissionsPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getMe()
      .then((me) => {
        if (active) {
          setUser(me);
        }
      })
      .catch(() => {
        if (active) {
          setUser(null);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Si el logout falla en red, igual cerramos la sesión local.
    }
    setUser(null);
  }

  return (
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <AppRoutes user={user} loading={loading} onLogin={setUser} onLogout={handleLogout} />
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}
