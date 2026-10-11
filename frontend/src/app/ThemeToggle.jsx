import { useTheme } from "../theme/ThemeProvider.jsx";

export default function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className={`btn btn-soft btn-sm d-inline-flex align-items-center gap-2 ${className}`.trim()}
      onClick={toggleTheme}
      aria-label={isDark ? "Activar tema claro" : "Activar tema oscuro"}
      title={isDark ? "Tema claro" : "Tema oscuro"}
      data-testid="theme-toggle"
    >
      <i className={`bi ${isDark ? "bi-sun-fill" : "bi-moon-stars-fill"}`} aria-hidden="true" />
      <span className="d-none d-sm-inline">{isDark ? "Claro" : "Oscuro"}</span>
    </button>
  );
}
