# Tasks

## 1. Tooling — contrato de design system para agentes y skills

- [x] 1.1 Crear `.opencode/skills/design-system/SKILL.md` (contrato para construir UI sobre `src/ui/` + tokens + `motion` + Bootstrap: cómo agregar un componente, color por rol, temas, micro-interacciones, evidencia); verificar que el frontmatter es YAML válido y que el trigger no colisiona con otras skills
- [x] 1.2 Actualizar `.opencode/agents/frontend.md` (estructura `src/app`/`src/ui`/`src/theme`, reutilizar tokens y componentes, sin CDN, accesibilidad, `data-testid`) y `.opencode/agents/reviewer.md` (checklist de design system, accesibilidad, light/dark, color por rol); verificar que ambos describen el estado real del frontend
- [x] 1.3 Actualizar `.opencode/skills/run-verification`, `.opencode/skills/create-crud` y `.opencode/skills/new-use-case` (build+lint de frontend, uso del design system en CUs con UI, evidencia light/dark); verificar coherencia con `AGENTS.md`
- [x] 1.4 Regenerar `.atl/skill-registry.md` incluyendo la skill `design-system`; verificar que aparece con su trigger y path

## 2. Fundaciones — dependencias, tokens y tema

- [x] 2.1 Agregar e instalar dependencias de frontend (`bootstrap`, `bootstrap-icons`, `motion`, `@fontsource/plus-jakarta-sans`); verificar `cmd /c npm run build` en `frontend/`
- [x] 2.2 Crear `frontend/src/theme/tokens.css` con tokens de color (marca, rol, semánticos, neutros) en claro y oscuro, mapeo a variables de Bootstrap y utilidades de animación/`prefers-reduced-motion`; verificar que el build compila
- [x] 2.3 Crear `frontend/src/theme/ThemeProvider.jsx` (contexto + `data-bs-theme` + `localStorage` `campus-theme` + default por `prefers-color-scheme`) y el script anti-flash en `index.html`; verificar build y que el tema se persiste al recargar
- [x] 2.4 Actualizar `frontend/src/main.jsx` (imports de Bootstrap CSS, Bootstrap Icons, tokens y tipografía) y agregar `<html lang="es" data-bs-theme>`; verificar build

## 3. Design system — componentes `src/ui/`

- [x] 3.1 Crear componentes base (`Button`, `Card`, `Badge`, `RoleBadge`, `PageHeader`, `Spinner`, `EmptyState`); verificar build
- [x] 3.2 Crear `DataTable` (encabezados, filas, estado vacío, acciones) y `FormField` (label + input/textarea + error); verificar build
- [x] 3.3 Crear interactivos sobre la API JS de Bootstrap: `Modal`, `ConfirmDialog`, `Toast` + `ToastProvider`; verificar build y que no haya warnings de React
- [x] 3.4 Crear barril `src/ui/index.js` y un `design-system.css` para estilos propios; verificar build

## 4. Shell de aplicación y migración de pantallas

- [x] 4.1 Crear `Navbar` (marca, chip de usuario con color de rol, toggle de tema, cerrar sesión) y `Sidebar` (navegación por rol, item activo); verificar build
- [x] 4.2 Crear `AppLayout` (navbar + sidebar + `<Outlet/>` + footer) con transición de página con `motion`; verificar build
- [x] 4.3 Mover `ProtectedRoute` a `src/app/` y recomponer `App.jsx` con providers (`ThemeProvider`, `ToastProvider`) y rutas (`/login`, `/register` públicas sin shell; `/courses` y `/` bajo el shell); verificar build
- [x] 4.4 Reestilizar `LoginForm` y `RegisterForm` con el design system y layout centrado (misma lógica y validación backend-as-source-of-truth); verificar build y que los errores del backend se siguen mostrando con `role="alert"`
- [x] 4.5 Reestilizar `CoursesPage` y `CourseForm` con el design system (`DataTable`, `Badge`, botones, `Modal`/`ConfirmDialog` para alta/edición) conservando la funcionalidad (listado, alta, edición, activar/desactivar, errores); verificar build

## 5. Verificación integrada y evidencia

- [x] 5.1 Ejecutar `cmd /c npm run build` y `cmd /c npm run lint:format` en `frontend/` y el smoke HTTP del CU vigente (`python scripts/verify.py --cu cu03`) sin regresiones; conservar salidas
- [x] 5.2 Capturar evidencia UI con Playwright en claro y oscuro (login, shell + tabla, modal, confirmación, toast) en `evidencias/design-system/` y verificar consola sin errores inesperados

## 6. Documentación, revisión, archivo y commits

- [x] 6.1 Actualizar `AGENTS.md` (mapa de archivos con `src/theme`/`src/ui`/`src/app`, convenciones de frontend, tabla de skills con `design-system`), `openspec/config.yaml` (contexto del design system) y `README.md`; verificar que reflejen el estado real
- [x] 6.2 Registrar `decisiones.md` (stack de UI, colores por rol, mecanismo de tema, animaciones, portabilidad de deps), `progreso.md`, `prompts_log.md` y `tiempos.md`
- [x] 6.3 Revisar con el subagente `reviewer` (o skill `review-use-case` inline si falla por tier) y corregir bloqueantes hasta APROBADO; persistir `reviews/frontend-design-system.md` con hallazgos, severidad, veredicto y mapa de evidencia
- [x] 6.4 Archivar el cambio (`openspec archive add-frontend-design-system --yes`) y verificar `openspec validate --specs --strict`; cerrar `track-time` y commitear por unidad de trabajo (conventional commits), con `git status` limpio
