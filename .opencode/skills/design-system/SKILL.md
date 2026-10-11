---
name: design-system
description: "Trigger: crear o editar una pantalla o componente de UI, usar el design system, tema claro/oscuro, color por rol, animaciones de la interfaz. Construye UI del Campus Virtual sobre los tokens y componentes compartidos."
license: MIT
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar cuando se cree o modifique cualquier interfaz del frontend: una pantalla de feature, un componente visual, el shell de la aplicación, el tema o el color por rol.

## Hard Rules

- No inventar colores: usar SIEMPRE los tokens de `frontend/src/theme/tokens.css` (marca, rol, semánticos, neutros) o clases semánticas. Prohibido hardcodear valores hex/rgb en JSX o CSS de componente.
- No reimplementar lo que el design system ya cubre: botón, tarjeta, badge, badge de rol, tabla, campo de formulario, modal, confirmación, toast, spinner, estado vacío. Usar `frontend/src/ui/`.
- Bootstrap y Bootstrap Icons por npm (sin CDN). Iconos con `<i className="bi bi-<nombre>" />`. No cargar recursos por red.
- Animaciones: `motion` (`motion/react`) para lo estructural (transiciones de ruta, modal/toast, `layout` de listas) y CSS para micro-interacciones. Todo respeta `prefers-reduced-motion` (`useReducedMotion` + media query global).
- Accesibilidad: `label` asociado a cada control, `role="alert"` para errores del backend, foco visible y contraste suficiente.
- La validación del servidor es la fuente de verdad; el cliente solo envía y muestra los errores devueltos.
- Textos de UI en español; código e identificadores en inglés; sin comentarios salvo decisión no evidente.

## Estructura de referencia

- `frontend/src/theme/tokens.css` — tokens en `:root` (claro) y `[data-bs-theme="dark"]` (oscuro) + mapeo a variables de Bootstrap.
- `frontend/src/theme/ThemeProvider.jsx` — contexto de tema (`data-bs-theme`, `localStorage` `campus-theme`, default `prefers-color-scheme`).
- `frontend/src/ui/` — componentes reutilizables + `design-system.css` + barril `index.js`.
- `frontend/src/app/` — shell (`AppLayout`, `Navbar`, `Sidebar`, `ProtectedRoute`).
- `frontend/src/features/<feature>/` — pantallas y su cliente de API.

## Execution Steps

1. Leer el CU o el objetivo y revisar los componentes de `src/ui/` y tokens existentes antes de escribir.
2. Reutilizar componentes; si falta uno, agregarlo a `src/ui/` (no inline en la feature) y exportarlo en el barril.
3. Usar color por rol con `RoleBadge`/tokens; no introducir colores nuevos.
4. Componer la pantalla dentro del shell; si es pública (login/register), usar el layout centrado sin shell.
5. Mantener estables los textos accesibles y `data-testid` que usa la evidencia Playwright.
6. Verificar con `run-verification` (build + `lint:format`); capturar evidencia light/dark cuando corresponda al CU.

## Output Contract

Archivos creados/modificados con referencias `archivo:línea`, componentes reutilizados vs. nuevos, tokens usados, y resultado real del build/lint/evidencia. Está prohibido declarar "listo" sin la verificación ejecutada.

## References

- `openspec/specs/frontend-design-system/spec.md` — requisitos y escenarios del design system.
- `.opencode/agents/frontend.md` — reglas del subagente frontend.
