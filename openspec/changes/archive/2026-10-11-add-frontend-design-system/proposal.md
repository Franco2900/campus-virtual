# Proposal

## Why

El frontend del Campus Virtual hoy es HTML sin estilos: no hay CSS, ni librería de UI, ni iconos, ni un layout común. Cada pantalla (login, registro, cursos) se armó con `<section>`/`<table>` desnudos y estilos del navegador. Con siete casos de uso restantes por delante (CU-04 a CU-10), todos con componente visual, seguir así obliga a reescribir cada pantalla y a inventar estilos sueltos, lo que produce inconsistencias, retrabajo y una revisión imposible de sostener.

Este cambio establece una base visual única y reutilizable: tokens de diseño (color, tipografía, espaciado), un sistema de componentes sobre Bootstrap, un shell de aplicación (navbar, sidebar por rol, tema claro/oscuro) y animaciones consistentes. CU-04 en adelante consumen esa base en lugar de improvisar. No es estética decorativa: es infraestructura de frontend para que los CUs siguientes sean rápidos, consistentes y verdes en revisión.

## What Changes

- Incorporar Bootstrap y Bootstrap Icons por npm (sin CDN, por portabilidad) y `motion` (Framer Motion) para animaciones estructurales, con CSS propio para micro-interacciones.
- Introducir una tipografía empaquetada por npm (Plus Jakarta Sans).
- Definir tokens de diseño como CSS variables en `src/theme/tokens.css`, con tema claro y oscuro, y un color semántico por rol (Estudiante, Profesor, Administrador).
- Proveer un `ThemeProvider` que aplica el tema (`data-bs-theme`), lo persiste en `localStorage` y lo inicializa desde `prefers-color-scheme`.
- Crear un design system reutilizable en `src/ui/`: botones, cards, badges (incluido `RoleBadge` con color e ícono por rol), tabla de datos, campos de formulario, modal, diálogo de confirmación, toasts, spinner/skeleton, estado vacío y encabezado de página.
- Introducir un shell de aplicación en `src/app/`: layout con navbar (chip de usuario con color de rol, toggle de tema, logout), sidebar de navegación por rol y ruta protegida por rol, más los providers (tema, toasts, router) en `App.jsx`.
- Migrar las pantallas existentes (login, registro, cursos) al design system y al shell, sin cambiar su lógica de negocio ni su contrato de API.
- Actualizar el tooling de agentes y skills del proyecto para que el nuevo contrato visual sea la convención vigente (skill `design-system`, `frontend.md`, `reviewer.md`, `run-verification`, `create-crud`, `new-use-case`, registro de skills).
- **Fuera de alcance:** pantalla de usuarios (CU-04); cualquier cambio de backend, esquema o API; internacionalización; tests unitarios de componentes (se mantiene build + evidencia UI).

## Capabilities

### New Capabilities

- `frontend-design-system`: base visual reutilizable del frontend (tokens, componentes, shell de aplicación, tema claro/oscuro, color por rol y animaciones) sobre la que se construyen todas las pantallas del Campus Virtual.

### Modified Capabilities

Ninguna.

## Impact

- **Dependencias (frontend):** nuevas dependencias `bootstrap`, `bootstrap-icons`, `motion`, `@fontsource/plus-jakarta-sans`. Sin cambios en backend.
- **Frontend:** nuevos `src/theme/tokens.css`, `src/theme/ThemeProvider.jsx`, `src/ui/*` (sistema de componentes), `src/app/` (shell: `AppLayout`, `Navbar`, `Sidebar`, `ProtectedRoute`); `src/main.jsx` (imports de CSS/Icons/tokens) y `src/App.jsx` (providers, composición del shell). Reestilización de `src/features/auth/*` y `src/features/courses/*` sin cambiar su lógica.
- **Tooling:** nueva skill `.opencode/skills/design-system/`; actualización de `.opencode/agents/frontend.md`, `.opencode/agents/reviewer.md`, `.opencode/skills/run-verification`, `.opencode/skills/create-crud`, `.opencode/skills/new-use-case`; regeneración de `.atl/skill-registry.md`.
- **Docs:** `AGENTS.md` (mapa de archivos, convenciones de frontend, tabla de skills), `decisiones.md` (stack de UI, colores por rol, animaciones, portabilidad de deps), `progreso.md`, `tiempos.md`, `prompts_log.md`, `README.md`, y contexto de `openspec/config.yaml`.
- **Verificación:** `npm run build` + `npm run lint:format` + evidencia Playwright (login/registro/cursos en tema claro y oscuro) en `evidencias/frontend/`.
