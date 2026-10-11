# Design

## Context

El frontend (React 19 + Vite 7 + `react-router-dom` 7) no tiene ninguna capa visual: `index.html` no carga estilos, `main.jsx` monta `App` directamente y cada feature renderiza HTML sin clases. CU-03 dejó un router mínimo y pantallas por rol, pero sin layout común ni componentes reutilizables. Este cambio introduce la base de UI que consumirán CU-04..CU-10. Ver `proposal.md - Why` y `specs/frontend-design-system/spec.md`.

## Goals / Non-Goals

**Goals:**
- Tokens de diseño únicos (color, rol, semánticos, neutros, tipografía, espaciado) en `src/theme/tokens.css`, con tema claro y oscuro.
- Sistema de componentes reutilizable en `src/ui/` sobre Bootstrap, sin `react-bootstrap`.
- Shell de aplicación en `src/app/`: navbar, sidebar por rol, área de contenido y footer, con guard de rol.
- Tema conmutable (claro/oscuro) persistido y respetando `prefers-color-scheme`.
- Color por rol como token, aplicado en `RoleBadge` y elementos de navegación.
- Animaciones: `motion` para lo estructural; CSS para micro-interacciones; todo respeta `prefers-reduced-motion`.
- Portabilidad: dependencias por npm, sin CDN ni fuentes por red.
- Contratos de tooling (agentes/skills) actualizados para que los CUs siguientes usen la base.

**Non-Goals:**
- Pantallas nuevas de dominio (CU-04 en adelante).
- Cambios de backend, API, autenticación o validaciones.
- Tests unitarios de componentes (se mantiene build + lint + evidencia Playwright).
- Internacionalización; los textos siguen en español.
- Rediseño de arquitectura por feature (se conserva `src/features/<feature>/`).

## Decisions

- **D-A — Bootstrap por npm, sin `react-bootstrap` ni CDN.** Se usa el paquete `bootstrap` (CSS) + `bootstrap-icons`. Los componentes interactivos (Modal, Offcanvas, Dropdown, Tooltip) se envuelven sobre la **API JS de `bootstrap`** dentro de `src/ui/`, con componentes controlados y `ref` para no pelear con el ciclo de render de React ni con `StrictMode`. Alternativa descartada: `react-bootstrap` (más peso y una capa extra de abstracción para lo que necesitamos) y CDN (rompe la portabilidad exigida en `AGENTS.md`).
- **D-B — Tokens como CSS variables.** `tokens.css` define variables en `:root` (tema claro) y en `[data-bs-theme="dark"]` (tema oscuro), mapeando además las variables de Bootstrap (`--bs-primary`, etc.) para que los componentes nativos del framework hereden la paleta. Así el color por rol y los semánticos se reutilizan en cualquier componente sin props de color ad-hoc. Alternativa descartada: CSS-in-JS (nueva dependencia y runtime) y utilidades inline (imposibilitan el tema oscuro centralizado).
- **D-C — Color por rol y paleta.** Marca índigo `#4F46E5` (light) / `#818CF8` (dark). Roles: Estudiante azul cielo `#0EA5E9`/`#38BDF8`; Profesor esmeralda `#10B981`/`#34D399`; Administrador magenta `#DB2777`/`#F472B6`. Semánticos: success `#16A34A`/`#4ADE80`, warning `#D97706`/`#FBBF24`, danger `#DC2626`/`#F87171`. Cada rol tiene variante "soft" para fondos de badge. El magenta del Admin se usa en acentos/badges con ícono, no como color de peligro, para no confundirse con `danger`.
- **D-C2 — Tipografía.** Plus Jakarta Sans empaquetada por npm (`@fontsource/plus-jakarta-sans`) e importada en `main.jsx`; sin Google Fonts por red. Fallback a la pila de sistema.
- **D-D — Tema claro/oscuro.** `ThemeProvider` setea `data-bs-theme` en `<html>`, persiste la preferencia en `localStorage` (clave `campus-theme`) y usa `prefers-color-scheme` como default cuando no hay preferencia guardada. Toggle en la navbar. Un script inline mínimo en `index.html` evita el "flash" de tema incorrecto al cargar.
- **D-E — Composición y shell.** `App.jsx` monta los providers (`ThemeProvider`, `ToastProvider`) y el `BrowserRouter`; `AppLayout` renderiza `Navbar` + `Sidebar` + `<Outlet/>` + footer. `ProtectedRoute` se mueve desde `App.jsx` a `src/app/`. Las rutas existentes (`/login`, `/register`, `/courses`) se conservan; las públicas no usan el shell (pantalla centrada). Se agrega la ruta `/` como dashboard con mensaje por rol.
- **D-F — Animaciones.** `motion` (`motion/react`) para transiciones de ruta (`AnimatePresence` + `useLocation`), entrada/salida de Modales/Toasts y `layout` en listas. CSS propio (`tokens.css`/`design-system.css`) para hover/focus y micro-interacciones. Un bloque global `@media (prefers-reduced-motion: reduce)` neutraliza animaciones; los componentes usan `useReducedMotion`.
- **D-G — Convención de clases y estilos.** Se usa el sistema de utilidades de Bootstrap (`d-flex`, `gap-*`, `text-*`, etc.) para layout inline, más un archivo de estilos del design system para lo que Bootstrap no cubre (tokens, animaciones, componentes propios). Los colores nunca se hardcodean en JSX: siempre vía token/clase semántica.
- **D-H — Estabilidad para evidencia.** Se conservan los textos y roles accesibles clave ("Cerrar sesión", "Cursos", `role="alert"`) y se agregan `data-testid` a los elementos que las pruebas Playwright necesitan ubicar de forma estable.
- **D-I — Tooling como unidad previa.** La skill `design-system` y la actualización de agentes/skills se hacen en la primera unidad, para que la implementación y la revisión se rijan por el mismo contrato desde el arranque.

## Risks / Trade-offs

- [Dependencias nuevas de frontend] → Autorizadas por el usuario; todas por npm y empaquetadas (build), sin red en runtime. Impacto acotado a `frontend/`.
- [Bootstrap JS imperativo bajo React `StrictMode`] → Se envuelve en componentes controlados con `ref` y efectos idempotentes; se evita instanciar plugins en cada render.
- [Doble fuente de estilos (Bootstrap + propios)] → Se fija la regla: utilidades Bootstrap para layout, tokens/estilos propios para marca y componentes. Documentado en la skill `design-system`.
- [`motion` puede tentar a sobre-animar] → Se limita a transiciones estructurales; performance y `prefers-reduced-motion` como criterio de aceptación.
- [Evidencia Playwright sensible al DOM] → Mitigado con `data-testid` y conservación de textos accesibles.
- [Aumento del bundle] → Aceptable para el TP; se importa solo lo necesario de `bootstrap-icons`/`motion` donde sea posible.

## Migration Plan

Sin migración de datos. Cambio exclusivamente de frontend + tooling. Despliegue: `npm install`, `npm run build`; dev con `npm run dev`. Rollback: revertir `package.json`/`package-lock.json`, eliminar `src/theme/` y `src/ui/`, y restaurar `App.jsx`/`main.jsx` previos (las pantallas existentes vuelven a su estado sin clases).

## Open Questions

Ninguna que afecte specs, enfoque o tareas.
