# Control de progreso

Estados permitidos: **Pendiente** | **En progreso** | **Completada** | **Bloqueada**.

Última actualización: 2026-10-11.

## Fases de configuración del entorno

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 1 | Documentación base (`AGENTS.md`, `README.md`, `casos_de_uso.md`, registros) | Completada |
| Fase 2 | `opencode.json` de proyecto (MCP filesystem, permisos) | Completada |
| Fase 3 | Subagentes especializados en `.opencode/agents/` | Completada |
| Fase 4 | Skills reutilizables en `.opencode/skills/` | Completada |
| Fase 5 | Git + repositorio en GitHub | Completada |
| Fase 6 | Implementación de casos de uso (requiere OK docente y openspec inicializado) | En progreso |

## Infraestructura transversal

| Componente | Estado | Notas |
|------------|--------|-------|
| Design system de frontend (`src/theme`, `src/ui`, shell `src/app`) | Completada | Bootstrap + tokens claro/oscuro + `motion`; ciclo `add-frontend-design-system` (D-019, D-020) |
| Migraciones de esquema (Flask-Migrate/Alembic) | Completada | `backend/migrations/` con baseline pre-CU-04 + `0002`/`0003` (D-023) |

## Casos de uso

| ID | Nombre | Estado | Notas |
|----|--------|--------|-------|
| CU-01 | Registrarse | Completada | Implementado end-to-end; verificaciones y revisión pasadas; cambio `add-user-registration` archivado |
| CU-02 | Autenticarse | Completada | Implementado end-to-end; smoke HTTP 10/10 + UI Playwright; revisión APROBADA; cambio `2026-10-10-add-user-auth` archivado |
| CU-03 | Gestionar cursos | Completada | Implementado end-to-end; smoke 13/13 + UI Playwright; revisión APROBADA; cambio `2026-10-10-add-course-management` archivado |
| CU-04 | Gestionar usuarios | Completada | Implementado y verificado; 90 tests + smoke 21/21 + UI Playwright; revisión APROBADA y cambio archivado como `2026-10-11-add-user-management` |
| CU-05 | Gestionar inscripciones | Pendiente | Bloqueado hasta OK docente |
| CU-06 | Gestionar tareas | Pendiente | Bloqueado hasta OK docente |
| CU-07 | Entregar tarea | Pendiente | Bloqueado hasta OK docente |
| CU-08 | Corregir tarea | Pendiente | Bloqueado hasta OK docente |
| CU-09 | Consultar calificaciones | Pendiente | Bloqueado hasta OK docente |
| CU-10 | Filtrar usuarios | Pendiente | Bloqueado hasta OK docente |

## Resumen del agente (último)

- Fase 1 completada: documentación base del proyecto creada.
- Fase 2 completada: `opencode.json` de proyecto con el MCP `filesystem` (comando `cmd /c npx -y @modelcontextprotocol/server-filesystem`) y bloque de permisos. MCPs documentados en el README.
- Fase 3 completada: subagentes `backend`, `frontend`, `database`, `tester`, `reviewer` (read-only) en `.opencode/agents/`.
- Fase 4 completada: skills `track-time`, `new-use-case`, `create-crud`, `create-migration`, `run-verification` en `.opencode/skills/`. Registro actualizado en `.atl/skill-registry.md`.
- Fase 5 completada: repo `main` en GitHub **público** `https://github.com/Franco2900/campus-virtual` con 4 commits por unidad de trabajo (`chore`, `docs` x2, `feat`). Verificación previa OK: MCP `filesystem` conectado y acotado al proyecto, `context7` respondiendo, 5 subagentes y 5 skills registrados.
- **OK docente obtenido** para los 10 casos de uso (condición habilitante).
- Paso cero de la Fase 6: **openspec inicializado** (`openspec init` v1.13.2 con `--tools opencode --language es`): `openspec/config.yaml` (context, `strict_tdd: false` hasta que exista runner de tests, reglas por fase) + integración nativa para opencode (6 skills `openspec-*` y 6 comandos `/opsx-*`). Verificado: `openspec list` resuelve el root del proyecto, sin cambios activos.
- Decisiones registradas en `decisiones.md` (stack, arquitectura, MCPs, tiempos, openspec, comando MCP, set de skills/agentes, repo, operación de openspec).
- Los casos de uso quedaron especificados en `casos_de_uso.md`.
- **CU-01 (Registrarse) implementado end-to-end:** backend Flask (Flask 3.1.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.54, Werkzeug, pytest 9.1.1) con `POST /api/auth/register` (201/400/409, email único case-insensitive, hash de contraseña, rol Estudiante forzado) y 21 tests pasando; frontend React 19 + Vite 7 con proxy `/api` y pantalla de registro; smoke end-to-end verificado (alta 201 + duplicado 409 vía proxy). Decisión D-010.
- **CU-02 (Autenticarse) implementado y verificado:** API `POST /api/auth/login` (cookie de sesión firmada de Flask, D-011), `GET /api/auth/me` (protegido por `@login_required`) y `POST /api/auth/logout` (idempotente). Backend con 32 tests en `backend/tests/test_auth.py`; frontend con pantalla de login con toggle a registro y barra de sesión (nombre + rol + "Cerrar sesión"); smoke end-to-end **10/10 PASS** vía `scripts/verify.py` (readiness + proxy + cleanup garantizado) y smoke de UI con Playwright (registro → login → header con rol Estudiante → logout → error renderizado del backend) con screenshots en `evidencias/cu-02/`. Cierre: revisión APROBADA, cambio `add-user-auth` archivado y commits finales.
- **Gotcha de tooling resuelto:** en Windows, terminar `npm.cmd` dejaba el `node vite` hijo huérfano escuchando en `:5173`; los servicios lanzados no sobreviven a un reinicio de opencode ni a un tool call abortado. Solución: `scripts/verify.py` (**generalizado**, `--cu` y `--diagnose` para diagnóstico read-only) con pre-condición de puertos libres y cleanup del árbol de procesos (ver `errores.md`).
- **CU-02 cerrado:** backtrack 6.1 y 6.2 `[x]`, smoke HTTP 10/10 PASS y smoke de UI con Playwright (4 screenshots en `evidencias/cu-02/`), revisión del checklist `reviewer` sin bloqueantes (el subagente `reviewer` volvió a fallar por tier del proveedor; revisión inline aceptada), cambio `add-user-auth` archivado como `2026-10-10-add-user-auth` (`openspec validate --specs --strict` → 1 passed) y 6 commits por unidad de trabajo. Próximo: **CU-03 (Gestionar cursos)**.
- **CU-03 (Gestionar cursos) implementado y verificado (cierre en curso):** ciclo spec-driven `add-course-management` (proposal/specs/design/tasks). Backend: modelo `Course` (`code` único case-insensitive, `active` con baja lógica), `course_service` con validaciones en `services/` (400/403/404/409) y blueprint `courses` (`GET/POST /api/courses`, `GET/PUT/PATCH /api/courses/<id>`) protegido por `@login_required` + `@require_roles(UserRole.ADMIN)`. Bootstrap del Administrador con `scripts/seed_admin.py` (env obligatorio, idempotente, 4 cursos demo) — D-017. Frontend: ruteo con `react-router-dom` y pantalla de cursos (listado con estado, alta, edición, activar/desactivar) — D-018. Verificación: **55 tests** backend, `npm run build` + Prettier OK, smoke end-to-end **13/13 PASS** y evidencia UI Playwright (7 screenshots en `evidencias/cu-03/`). `scripts/verify.py` ahora corre contra una **base temporal aislada** con seed del admin.
- **Bug detectado y corregido vía evidencia UI:** el registro no emite cookie de sesión, pero el frontend asumía sesión al registrar; se corrigió para navegar a `/login` tras el registro (ver D-018).
- **CU-03 cerrado:** revisión APROBADA (skill `review-use-case` inline, sin bloqueantes; `reviews/cu-03.md`), cambio archivado como `2026-10-10-add-course-management` (`openspec validate --specs --strict` → 2 passed), y commits por unidad de trabajo. Próximo: **CU-04 (Gestionar usuarios)**.
- **Design system de frontend implementado y verificado:** ciclo spec-driven `add-frontend-design-system` (proposal/specs/design/tasks). Dependencias npm (`bootstrap`, `bootstrap-icons`, `motion`, `@fontsource/plus-jakarta-sans`, sin CDN). `src/theme/tokens.css` (tokens de marca/rol/semánticos/neutros en claro y oscuro, mapeo a Bootstrap 5.3) y `ThemeProvider` (`data-bs-theme` + `localStorage` `campus-theme` + `prefers-color-scheme` + script anti-flash). Design system en `src/ui/` (`Button`, `Card`, `Badge`, `RoleBadge`, `PageHeader`, `Spinner`, `EmptyState`, `DataTable`, `FormField`, `Modal`, `ConfirmDialog`, `Toast`+`ToastProvider`). Shell en `src/app/` (`AppLayout`, `Navbar` con chip de rol y toggle de tema, `Sidebar` por rol, `ProtectedRoute`, `HomePage`) con transición de página vía `motion`. Pantallas de auth y cursos migradas al design system (lógica y validación backend-as-source-of-truth intactas). Tooling: skill `design-system` + agentes/skills actualizados + registry. Decisión D-019 y D-020. Verificación: `npm run build` y `npm run lint:format` OK; smoke HTTP CU-03 13/13 sin regresiones; evidencia Playwright claro/oscuro (login, shell+tabla, modal, confirmación, toast) en `evidencias/design-system/`. Revisión APROBADA y cambio archivado como `2026-10-11-add-frontend-design-system`.
- **CU-04 (Gestionar usuarios) implementado y verificado (cierre en curso):** ciclo spec-driven `add-user-management` (proposal/specs/design/tasks). Decisiones acordadas con el usuario: el Admin gestiona datos + rol + `active` + reset de contraseña; Profesor↔curso entra en CU-04; migraciones con Flask-Migrate; autogestión bloqueada con 400. Backend: `models/user.py` con `active`; `user_service.py` (listado, detalle, edición con guard de autogestión, activar/desactivar, reset, validaciones en `services/`) y `blueprints/users.py` (`GET/POST` de `/api/users`); `models/course_teacher.py` (tabla asociativa N:M, `UNIQUE(course_id, teacher_id)`) y `course_teacher_service.py` con `GET/POST/DELETE /api/courses/<id>/teachers`; `auth_service` rechaza cuentas inactivas en login y sesión. Migraciones Alembic adoptadas: baseline `0001_baseline_pre_cu_04` + stamp de la base real, `0002` (`user.active` con `server_default`) y `0003` (`course_teacher`). Frontend: features `users/` (api, `UsersPage`, `UserForm`, `ResetPasswordForm`) y `courses/CourseTeachers.jsx` + botón "Profesores" en `CoursesPage`; ruta `/users` y ítem de sidebar. Decisiones D-021/D-022/D-023; ajuste de D-010. Verificación: **90 tests** backend, `ruff` y Prettier OK, `npm run build` OK, smoke end-to-end **21/21 PASS** (`scripts/smoke_cu04.py`) y evidencia UI Playwright claro/oscuro (9 screenshots en `evidencias/cu-04/`). Revisión APROBADA (`reviews/cu-04.md`) y cambio archivado como `2026-10-11-add-user-management`.

## Próximos pasos

1. **CU-05 (Gestionar inscripciones)** orquestado por la skill `new-use-case`.
2. Resolver el tier del proveedor para el subagente `reviewer` (falló en CU-01, CU-02, CU-03 y CU-04; se cerró con revisión inline) y reintentarlo en el próximo CU.

## Pendientes de definición

- Punto de integración del chatbot.
