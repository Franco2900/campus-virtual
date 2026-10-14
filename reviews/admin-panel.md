# Review — panel de inicio del Administrador y unificación de badges de estado

- **Fecha:** 2026-10-14
- **Cambio:** panel de inicio del Administrador + unificación de los badges de estado activo/inactivo (no es un CU y no tiene cambio OpenSpec asociado)
- **Revisor:** inline vía skill `review-use-case` (el subagente `reviewer` sigue fallando por tier del proveedor: "OpenCode's free tier can only be used from within OpenCode"; ver `errores.md`)
- **Veredicto:** APROBADO

## Alcance revisado

- `frontend/src/ui/`: `PageHeader.jsx` (fix de la prop `icon`), `StatCard.jsx` (nuevo), `StatusBadge.jsx` (nuevo), `index.js`, `design-system.css`.
- `frontend/src/app/`: `AdminHomePage.jsx` (nuevo), `Sidebar.jsx`, `App.jsx`.
- `frontend/src/features/`: `courses/CoursesPage.jsx`, `users/UsersPage.jsx`, `tasks/TasksPage.jsx`, `enrollments/EnrollmentsPage.jsx`.
- `.opencode/skills/design-system/SKILL.md` (reglas actualizadas con lo verificado acá).

No se tocó backend ni esquema.

## Cumplimiento de las reglas del design system

| Regla | Estado | Evidencia |
|-------|--------|-----------|
| Sin colores hardcodeados | OK | diff de `design-system.css` (55 líneas agregadas) sin literales de color; el único `rgba(` es `rgba(var(--campus-brand-rgb), 0.18)`. `StatusBadge`/`StatCard` no definen color propio |
| No reimplementar componentes cubiertos | OK | `StatusBadge` reutiliza `Badge` (tonos `success`/`warning`); `StatCard` reutiliza `Card` y `Link` de `react-router-dom`; ninguna pantalla arma chips a mano |
| Componente nuevo en `src/ui/` + barril | OK | `StatCard.jsx` y `StatusBadge.jsx` agregados a `frontend/src/ui/index.js`; las features los importan solo desde el barril |
| Reutilizar tokens y no introducir colores por rol nuevos | OK | colores por rol siguen saliendo de `RoleBadge`/`roles.js`; las métricas usan `--campus-brand` y las variantes `-soft` ya existentes |
| Temas claro/oscuro | OK | las 13 capturas se tomaron en ambos temas con `data-bs-theme` aplicado; los valores computados cambian por tema (tabla de abajo) |
| `data-testid` estable para la evidencia | OK | `admin-home`, `stat-courses|users|students|teachers|admins`, `quick-link-*`, `course-option-<id>`, `student-results`, `course-select`, `task-row-<id>` |
| Textos de UI en español, código en inglés | OK | etiquetas `Activo`/`Inactivo`/`Activa`/`Inactiva`/`Inscripto activo`/`Sin inscripción`; identificadores en inglés |

La spec `openspec/specs/frontend-design-system/spec.md` enumera los componentes como "al menos" esos, así que agregar `StatCard` y `StatusBadge` no la contradice; la spec no se modificó.

## Hallazgos

| Archivo:línea | Severidad | Hallazgo | Estado |
|---------------|-----------|----------|--------|
| `frontend/src/ui/PageHeader.jsx:7` | Media | Anteponía `bi bi-` a una prop que las 6 pantallas ya pasan con la clase completa (`icon="bi-journal-text"`), generando `class="bi bi bi-journal-text"`: el icono del encabezado no se dibujaba en ninguna pantalla con `PageHeader` | Corregido a `bi ${icon}`; verificado en runtime (ancho 25,61 px en `/`, `/courses`, `/enrollments`, `/tasks`) |
| `frontend/src/ui/Badge.jsx` (uso) | Media | El mismo estado "inactivo" se veía distinto según la pantalla: `slash-circle` + tono `danger` en Cursos/Usuarios y `pause-circle-fill` + `warning` en Inscripciones; además el texto era `inactivo` (minúscula) en algunos lugares | Corregido con `StatusBadge` (`warning` + `pause-circle-fill` como criterio único); `slash-circle` ya no aparece en `frontend/src` |
| `frontend/src/features/enrollments/EnrollmentsPage.jsx:368` | Baja | El estado del curso inactivo en la lista se mostraba como `inactivo` en minúscula | Corregido: usa `StatusBadge` (`Inactivo`) |
| `frontend/src/App.jsx:19-24` | Media | El Administrador aterrizaba en `HomePage`, que mostraba "Próximamente — Todavía no hay secciones disponibles para tu rol" aunque ya existían Cursos, Inscripciones y Usuarios | Corregido: `HomeRoute` renderiza `AdminHomePage` para el rol admin |
| `frontend/src/app/AdminHomePage.jsx` | Baja | Las tarjetas de métrica mostraban `Activos`/`Inactivos` en una sola línea, difícil de leer | Corregido: `StatCard.detail` acepta lista y renderiza una línea por dato |

No quedan hallazgos bloqueantes ni altos abiertos de este alcance.

## Evidencia verificada

Capturas en `evidencias/admin-panel/` (Playwright, tema claro y oscuro, `fullPage`):

| Archivo | Qué muestra |
|---------|-------------|
| `01-inicio-admin-light.png`, `01-inicio-admin-dark.png` | Inicio del Administrador: "Hola, Admin" + `RoleBadge`, 5 tarjetas de métrica con dos líneas (`Activos`/`Inactivos`) y 3 accesos rápidos |
| `02-cursos-estado-light.png`, `02-cursos-estado-dark.png` | Cursos: 9 `Activo` + 1 `Inactivo` (HIST1) |
| `03-inscripciones-curso-inactivo-light.png`, `03-inscripciones-curso-inactivo-dark.png` | Inscripciones con HIST1 seleccionado: chip `Inactivo` del curso + aviso de curso inactivo |
| `04-inscripciones-inscriptos-light.png` | Inscripciones con PROG1: 6 `Inscripto activo` + 1 `Inscripto inactivo` + 9 `Sin inscripción` |
| `05-usuarios-estado-light.png`, `05-usuarios-estado-dark.png` | Usuarios: 23 `Activo` + 2 `Inactivo` (Fabián Molina / alumno6 y alumno18) |
| `06-inscripciones-docente-light.png`, `06-inscripciones-docente-dark.png` | Vista del Profesor: buscador `Inscribir estudiante` + lista de candidatos + botones `Desactivar`/`Quitar` |
| `07-tareas-estado-light.png`, `07-tareas-estado-dark.png` | Tareas (PROG1): 3 `Activa` + 1 `Inactiva` |

Medición determinística por `getComputedStyle` + `getBoundingClientRect()` (el screenshot solo no prueba el icono, porque `::before` serializa `content` vacío en Chrome):

| Estado | Vistas donde se midió | Clase del icono | Ancho | Claro (color / fondo) | Oscuro (color / fondo) |
|--------|------------------------|-----------------|-------|------------------------|-------------------------|
| Inactivo / Inactiva | Cursos HIST1, Inscripciones HIST1 (curso), Inscripciones PROG1 (inscripción), Usuarios (2), Tareas PROG1 | `bi bi-pause-circle-fill` | 15,20 px | `rgb(217, 119, 6)` / `rgb(254, 243, 199)` | `rgb(251, 191, 36)` / `rgb(69, 26, 3)` |
| Activo / Activa / Inscripto activo | Cursos (9), Usuarios (23), Tareas PROG1 (3), Inscripciones PROG1 (6) | `bi bi-check-circle-fill` | 15,20 px | `rgb(22, 163, 74)` / `rgb(220, 252, 231)` | `rgb(74, 222, 128)` / `rgb(5, 46, 22)` |
| Sin inscripción | Inscripciones (16 en HIST1, 9 en PROG1) | `bi bi-dash-circle` | — | tono `neutral` (concepto distinto: no es activo/inactivo) | ídem |

Los valores son idénticos entre las 4 pantallas y los 2 temas: eso es la prueba de la unificación (antes el mismo estado salía `danger`/`slash-circle` en una pantalla y `warning`/`pause-circle-fill` en otra).

Datos contra la base sembrada (`backend/instance/campus.db`, migración `0006`):

- Inicio del Administrador: Cursos 10 (9/1), Usuarios 25 (23/2), Estudiantes 18 (16/2), Docentes 6 (6/0), Administradores 1 (1/0) — coincide con los conteos reales.
- Inscripciones PROG1: 6 activos + 1 inactivo + 9 sin inscripción = 16 estudiantes activos; HIST1: 16 sin inscripción (curso sin inscripciones).
- Tareas PROG1: 4 filas (3 activas, 1 inactiva).
- Vista Profesor: `enroll-student-search` y `student-results` presentes; 7 botones `enrollment-action-*` (el Profesor conserva Activar/Desactivar).

Puertas ejecutadas:

- `npm run build` (dentro de `frontend/`) → PASS (4,00 s).
- `npm run lint:format` (Prettier) → "All matched files use Prettier code style!".
- Consola del navegador: sin errores inesperados; solo `401` de `/api/auth/me` (respuesta diseñada cuando no hay sesión, capturada en `App.jsx:102-106`) y los `500` de la corrida anterior en la que el backend estaba caído.
- Sesiones: `/` redirige a `/login` sin sesión (`ProtectedRoute`); login de Administrador y de Profesor OK; `/tasks` y `/submissions` siguen restringidos por rol.

Incidente durante la verificación (no es defecto del código): el backend se había detenido (nada escuchando en `5000`), y el `500` de `POST /api/auth/login` venía del proxy de Vite (`AggregateError [ECONNREFUSED]`, visible en `vite.err.log`). Se reinició el backend (`127.0.0.1:5000`) y se repitió la verificación completa; ambos servidores quedan levantados para revisión manual.

## Observaciones no bloqueantes

- `frontend/src/app/HomePage.jsx` (docente y estudiante) todavía usa tarjetas propias y muestra "Próximamente — Todavía no hay secciones disponibles para tu rol", hoy falso (esos roles ya tienen Cursos, Inscripciones, Tareas o Entregas). Candidato a reutilizar `StatCard` en un próximo cambio.
- `EnrollmentsPage.jsx` mantiene dos caminos de alta de estudiante: selector sobre `listUsers` para el Admin y buscador sobre `students` para el Profesor. Conviven bien, pero se pueden unificar al retomar esa pantalla.
- CRLF: con `core.autocrlf=true` y sin `.gitattributes`, `git status` marca archivos sin cambios reales; la fuente de verdad es `git diff --numstat`. Queda pendiente decidir si se agrega `.gitattributes` (`* text=auto eol=lf`) o `endOfLine: "auto"` en Prettier.

## Conclusión

APROBADO. El panel de inicio del Administrador reemplaza la pantalla engañosa anterior, el bug del icono de `PageHeader` quedó corregido y verificado en runtime, y el estado activo/inactivo se ve igual en Cursos, Inscripciones, Usuarios y Tareas, en tema claro y oscuro. Las puertas de build y formato pasan y la evidencia cubre cada afirmación con medición de DOM además del screenshot.
