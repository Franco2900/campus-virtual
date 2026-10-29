# AGENTS.md — Frontend

Alcance: `frontend/`. Las reglas compartidas están en el `AGENTS.md` de la raíz; este archivo no las repite.

## Estructura

- Organización por feature: `src/features/<feature>/`.
- `src/api/client.js` es el cliente HTTP base (incluye `postForm` para multipart).
- Design system propio sobre Bootstrap: tokens en `src/theme/tokens.css`, tema en `src/theme/ThemeProvider.jsx`, componentes en `src/ui/`, shell en `src/app/`.
- Componentes en `PascalCase`; módulos en `camelCase`.

## Design system

- Color por rol, semánticos y neutros como tokens; claro/oscuro vía `data-bs-theme` + `localStorage` (`campus-theme`).
- Componentes reutilizables: `Button`, `Card`, `Badge`, `RoleBadge`, `PageHeader`, `Spinner`, `EmptyState`, `DataTable`, `FormField`, `Modal`, `ConfirmDialog`, `Toast`.
- Regla: reutilizar tokens y componentes existentes. Sin colores hardcodeados, sin CDN.
- Animaciones con `motion` (D-020).
- `data-testid` en los elementos que la evidencia necesita.
- Contrato detallado en la skill `design-system`; cargarla antes de crear o editar una pantalla.

## Stack visual y accesibilidad

- Bootstrap y Bootstrap Icons por npm (sin CDN). Los componentes interactivos envuelven la API JS de Bootstrap (controlados con `ref`), no `data-bs-*` suelto.
- `label` por control, `role="alert"` para errores, foco visible, contraste suficiente y respeto por `prefers-reduced-motion`.
- Mantener estables los textos accesibles y los `data-testid` que usan las pruebas de evidencia (Playwright).
- Un componente nuevo de `src/ui/` se exporta en el barril.

## Reglas de la capa

- Las validaciones del servidor son la fuente de verdad: el cliente solo envía y muestra los errores que devuelve el backend.
- Sin lógica de negocio en el cliente: permisos, plazos y promedios vienen calculados del backend.
- El contrato de cada endpoint está en `docs/api.md`; leerlo antes de tocar una pantalla o el cliente HTTP.

## Comandos (dentro de `frontend/`)

- `npm install` y `npm run dev` → `http://localhost:5173`, con proxy `/api` → `http://localhost:5000`.
- Build: `npm run build`.
- Lint/formato: `npm run lint:format` (check) y `npm run lint:format:fix` (aplica).
- En Windows, prefijar con `cmd /c` por la execution policy (D-006).

## Convenciones

- `camelCase` para variables y funciones, `PascalCase` para componentes y sus archivos, módulos en `camelCase`.
- UI y mensajes al usuario en español (neutral); identificadores en inglés.
- Comentarios solo para decisiones o restricciones no evidentes.
