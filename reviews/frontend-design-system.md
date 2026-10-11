# Review — `add-frontend-design-system`

- **Fecha:** 2026-10-11
- **Cambio:** `openspec/changes/add-frontend-design-system` (infraestructura transversal, no es un CU)
- **Revisor:** inline vía skill `review-use-case` (el subagente `reviewer` volvió a fallar por tier del proveedor: "OpenCode's free tier can only be used from within OpenCode")
- **Veredicto:** APROBADO

## Alcance revisado

Spec `specs/frontend-design-system/spec.md` vs. implementación en `frontend/src/theme/`, `frontend/src/ui/`, `frontend/src/app/`, `frontend/src/App.jsx`, `frontend/src/main.jsx`, `frontend/index.html`, `frontend/public/favicon.svg` y pantallas migradas (`features/auth/`, `features/courses/`).

## Cumplimiento de la spec

| Requisito | Estado | Evidencia |
|-----------|--------|-----------|
| Tokens claro/oscuro | OK | `frontend/src/theme/tokens.css:1-85` (light `:root`, dark `[data-bs-theme="dark"]`), mapeo a vars de Bootstrap `:80-85` |
| Sin colores literales en componentes | OK | `grep '#[0-9a-fA-F]{3,8}'` sobre `frontend/src` → 44 matches, **todos** en `tokens.css`; `design-system.css` y todo JSX usan `var(--campus-*)` |
| Persistencia + detección de tema | OK | `frontend/src/theme/ThemeProvider.jsx:6-31` (`campus-theme`, `prefers-color-scheme`, `data-bs-theme`) |
| Anti-flash | OK | `frontend/index.html:8-23` (script inline replica la lógica stored ?? system) |
| Componentes reutilizables | OK | `frontend/src/ui/{Button,Card,Badge,RoleBadge,PageHeader,Spinner,EmptyState,DataTable,FormField,Modal,ConfirmDialog,Toast}.jsx` + barrel `index.js` |
| Diálogo de confirmación que no ejecuta sin confirmar | OK | `frontend/src/ui/ConfirmDialog.jsx`; usado en `features/courses/CoursesPage.jsx:186-201` |
| Shell + navegación por rol | OK | `frontend/src/app/{AppLayout,Navbar,Sidebar}.jsx`; `Sidebar.jsx` filtra `NAV_ITEMS` por rol |
| Protección de secciones + acceso sin sesión | OK | `frontend/src/app/ProtectedRoute.jsx:16-30` (redirect a `/login`; mensaje `role="alert"` si rol no autorizado) |
| Color por rol | OK | `frontend/src/ui/roles.js` + tokens `--role-student/teacher/admin` (`tokens.css:13-20,58-65`) |
| Animaciones que respetan `prefers-reduced-motion` | OK | override global `tokens.css:165-177` + `useReducedMotion` en `Toast.jsx:10,39-41` |
| Portabilidad (sin CDN, deps empaquetadas) | OK | fuentes `@fontsource` y `bootstrap-icons` bundleados en `dist/` (build 2026-10-11: `bootstrap-icons-*.woff2`, `plus-jakarta-sans-*.woff2`) |

## Regresiones en pantallas migradas

- **Auth:** registro NO inicia sesión → `RegisterForm` llama `onSuccess(user)` (`RegisterForm.jsx:33`) pero `RegisterPage.jsx:17` navega a `/login`. Login setea usuario y la ruta `/` reenvía admin a `/courses` (`App.jsx:14-19,26,37`). Errores de backend con `role="alert"` (`LoginForm.jsx:63`, `RegisterForm.jsx:89`).
- **Cursos:** listado/alta/edición/activar-desactivar preservados; `CourseForm` desactiva la validación nativa (`noValidate`) y muestra el error del backend (`CourseForm.jsx:41,70-74`). Toggle vía `ConfirmDialog` + toast (`CoursesPage.jsx:64-88`).
- Sin hallazgos bloqueantes.

## Hallazgos

| # | Archivo:línea | Severidad | Hallazgo | Estado |
|---|---------------|-----------|----------|--------|
| H1 | `frontend/src/ui/ConfirmDialog.jsx:13,39` vs `frontend/src/features/courses/CoursesPage.jsx:190` | Media | Inconsistencia de contrato de íconos: `ConfirmDialog` esperaba el nombre completo (`bi-question-circle`) pero `CoursesPage` pasaba nombre base (`toggle-off`/`toggle-on`) → el ícono no se renderizaba. | **Corregido**: `ConfirmDialog` ahora antepone `bi-` (convención `bare name`, igual que `Button`/`Badge`); default `question-circle` |
| H2 | `frontend/src/ui/Toast.jsx:69` | Baja | `aria-label="Cerrar notificacion"` sin tilde. | **Corregido** → "Cerrar notificación" |
| H3 | `frontend/src/ui/ConfirmDialog.jsx:11` | Baja | `title` por defecto "Confirmar accion" sin tilde. | **Corregido** → "Confirmar acción" |
| H4 | `frontend/src/theme/ThemeProvider.jsx:30` | Baja (observación) | El tema derivado del sistema se persiste en el primer arranque, por lo que si el SO cambia de preferencia luego, la app no la sigue hasta que el usuario togglee. La spec solo exige que el tema inicial coincida con `prefers-color-scheme` cuando el usuario nunca eligió; se cumple. | Aceptado |

### Convención de íconos (nota para próximos CU)

Conviven dos convenciones: componentes que **anteponen** `bi-` (`Button`, `Badge`, `ConfirmDialog` — reciben `"pencil"`) y componentes que **reciben** el nombre completo (`EmptyState`, `DataTable`, `PageHeader` — reciben `"bi-inbox"`). Al usar la skill `design-system` en CU-04+, respetar la convención de cada componente.

## Evidencia verificada

- `cmd /c npm run build` → OK (built in 3.41s; `index-*.js` 435.84 kB, `index-*.css` 339.48 kB).
- `cmd /c npm run lint:format` → "All matched files use Prettier code style!".
- Smoke HTTP CU-03 `13/13 PASS` sin regresiones (`scripts/verify.py --cu cu03 --keep`).
- UI Playwright (servicios vivos): login → `/courses`; shell + tabla + chip de rol; toggle a oscuro persiste (`data-bs-theme=dark`, `localStorage campus-theme=dark`); modal "Nuevo curso"; `ConfirmDialog` + toast en desactivar/reactivar PROG1; logout → `/login`. Consola sin errores inesperados (solo `401` esperado de `GET /api/auth/me` sin sesión).
- Screenshots en `evidencias/design-system/`: `01-login-light.png`, `02-courses-light.png`, `03-courses-dark.png`, `04-modal-dark.png`, `05-confirm-dark.png`, `06-toast-dark.png`, `07-login-dark.png`, `08-register-light.png` (8/8 existen, no vacíos).

## Conclusión

Sin hallazgos Bloqueantes. Las tres correcciones (H1–H3) son cosméticas y ya aplicadas; H4 es una observación aceptada. El cambio cumple la spec y no introduce regresiones de comportamiento. **APROBADO** para archivar.
