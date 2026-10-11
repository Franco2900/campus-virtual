# Registro de prompts

Auditoría de los prompts utilizados con agentes de IA. Permite reproducir cómo se llegó a una implementación.

Formato de cada entrada:

- **Fecha:** `YYYY-MM-DD HH:MM`.
- **Contexto / CU / tarea.**
- **Prompt utilizado.**
- **Resumen de la respuesta.**
- **Archivos modificados.**
- **Resultado.**
- **Estado:** Pendiente / En progreso / Completado.
- **Verificaciones realizadas.**

---

## 2026-10-09 11:45 — Inicialización del proyecto

- **Contexto / tarea:** Fase 0-1. Definición del entorno de trabajo con IA (MCPs, skills, plan).
- **Prompt utilizado (resumen):** "Vamos a hacer un proyecto de un campus virtual... recomienda qué MCP y skills implementar... usar MCP de Memoria, Filesystem/Terminal y Documentación... medir tiempos en un archivo aparte... proponer un plan."
- **Resumen de la respuesta:** análisis de `Casos de uso.txt`, `Consignas TP.txt` y la plantilla; recomendación de MCPs (engram, context7, filesystem) y skills; diseño de `tiempos.md`; plan por fases; arquitectura de backend.
- **Archivos modificados:** ninguno (modo plan).
- **Resultado:** plan aprobado; decisiones D-001 a D-005.
- **Estado:** Completado.
- **Verificaciones:** no aplica.

## 2026-10-09 11:55 — Fase 1: documentación base

- **Contexto / tarea:** Fase 1. Creación de la documentación base del proyecto.
- **Prompt utilizado:** "Empezá con la fase 1."
- **Resumen de la respuesta:** se crean `tiempos.md`, `casos_de_uso.md`, `AGENTS.md`, `README.md`, `decisiones.md`, `errores.md`, `progreso.md` y `prompts_log.md`.
- **Archivos modificados:** ver lista anterior.
- **Resultado:** documentación base creada con los PENDIENTE DE DEFINIR marcados.
- **Estado:** Completado.
- **Verificaciones:** revisión de presencia y contenido de los archivos creados.

## 2026-10-09 12:02 — Fase 2: configuración de proyecto

- **Contexto / tarea:** Fase 2. `opencode.json` de proyecto con MCP de filesystem y permisos.
- **Prompt utilizado:** "Arranca con la fase 2."
- **Resumen de la respuesta:** se creó `opencode.json` con el MCP local `filesystem` (`cmd /c npx -y @modelcontextprotocol/server-filesystem "<ruta>"`) y un bloque de permisos. Se verificó `npx` (falla por execution policy en PowerShell; un spawn directo da `ENOENT`, por eso se usa `cmd /c`), la existencia del paquete (v2026.8.31) y el arranque real del server (`Secure MCP Filesystem Server running on stdio`). Se documentaron los MCP en el README y AGENTS.md.
- **Archivos modificados:** `opencode.json` (nuevo), `README.md`, `AGENTS.md`, `decisiones.md` (D-006), `progreso.md`, `tiempos.md`, `prompts_log.md`.
- **Resultado:** configuración de proyecto lista; requiere reinicio de opencode.
- **Estado:** Completado.
- **Verificaciones:** JSON parseado con Node; arranque del server MCP probado con `Start-Process`.

## 2026-10-09 12:11 — Fase 3 + 4: subagentes y skills

- **Contexto / tarea:** Fase 3 y 4. Subagentes especializados y skills reutilizables.
- **Prompt utilizado:** "Antes de crear las skills y subagentes, no te olvides que el proyecto debe andar en cualquier sistema operativo y que siempre me tenes que recomendar skills o subagentes cuando creas que haga falta."
- **Resumen de la respuesta:** se crearon 5 subagentes (backend, frontend, database, tester, reviewer read-only) y 5 skills (track-time, new-use-case, create-crud, create-migration, run-verification) siguiendo el style-guide LLM-first. Se regeneró `.atl/skill-registry.md` y se agregó la sección `Portabilidad` a AGENTS.md, aclarando que `opencode.json` es tooling local de la máquina.
- **Archivos modificados:** `.opencode/agents/*.md`, `.opencode/skills/*/SKILL.md`, `.atl/skill-registry.md`, `AGENTS.md`, `decisiones.md` (D-007), `progreso.md`, `tiempos.md`, `prompts_log.md`.
- **Resultado:** entorno de agentes/skills listo.
- **Estado:** Completado.
- **Verificaciones:** style-guide aplicado; registro regenerado y persistido en memoria.

## 2026-10-09 12:19 — Fase 5: git + GitHub

- **Contexto / tarea:** Fase 5. Control de versiones y repositorio remoto.
- **Prompt utilizado:** "Verifica que los mcp, los subagentes y las skills antes de seguir con la proxima fase. No te olvides de indicarme cuando debo inicializar openspec" (verificación previa) y "Arranca con la fase 5".
- **Resumen de la respuesta:** verificación en vivo de los 3 MCP (filesystem acotado al proyecto, engram operativo, context7 resolvió Flask), 5 subagentes y 5 skills; luego `git init` + `git branch -M main`, `.gitignore` (incl. `.atl/`), 4 commits por unidad de trabajo, `gh auth login` (Franco2900), repo público `campus-virtual`, push y sincronización de `main` con `origin/main`. Se indicó que openspec se inicializa tras el OK docente y antes de CU-01.
- **Archivos modificados:** `.gitignore` (nuevo), `progreso.md`, `tiempos.md`, `prompts_log.md`, `decisiones.md` (D-008), `README.md`.
- **Resultado:** Fase 5 completada; repo `https://github.com/Franco2900/campus-virtual`.
- **Estado:** Completado.
- **Verificaciones:** `gh auth status` OK; `git status -sb` limpio y sincronizado con `origin/main`; `gh repo view` confirma `PUBLIC` y `main`.

## 2026-10-09 12:43 — Fase 6, paso cero: inicializar openspec

- **Contexto / tarea:** Fase 6. Inicializar openspec como fuente de verdad de specs (OK docente obtenido).
- **Prompt utilizado:** "Ya tengo el ok del docente" → se investigó el flujo y se preguntó el modo de operación ("Aprobado, inicialo").
- **Resumen de la respuesta:** investigación previa (CLI `openspec` v1.13.2 vía `cmd /c`; skills `sdd-*` = convención openspec, no sistema competidor → D-005 Superada por D-009). Se ejecutó `openspec init --tools opencode --language es --force --no-copilot-cloud`, que generó `openspec/` (config.yaml, specs/, changes/archive/), 6 skills `openspec-*` y 6 comandos `/opsx-*` en `.opencode/`, más un mini node project que su `.gitignore` propio mantiene fuera de git. Se enriqueció `config.yaml` (context del proyecto, `strict_tdd: false`, reglas y operaciones por convención) y se actualizó el registro de skills.
- **Archivos modificados:** `openspec/config.yaml`, `.opencode/commands/opsx-*.md`, `.opencode/skills/openspec-*/SKILL.md`, `.atl/skill-registry.md`, `AGENTS.md`, `decisiones.md` (D-005 Superada, D-009), `progreso.md`, `tiempos.md` (T-006), `prompts_log.md`, `README.md`.
- **Resultado:** paso cero completado; proyecto listo para CU-01 vía `new-use-case`.
- **Estado:** Completado.
- **Verificaciones:** `openspec list --json` resuelve el root del proyecto; `openspec validate` sin cambios activos (esperado); skills/commands presentes en `.opencode/`.

## 2026-10-09 13:06 — CU-01: planning (openspec propose)

- **Contexto / tarea:** CU-01 (Registrarse). Generar el cambio `add-user-registration` con los 4 artefactos de planning (proposal, specs, design, tasks).
- **Prompt utilizado:** "Arrancá CU-01 con new-use-case" → aprobación de defaults de stack y "arranca" para el planning.
- **Resumen de la respuesta:** se creó el cambio, se escribieron `proposal.md`, `specs/user-auth/spec.md` (capability nueva), `design.md` (decisiones D-A..D-K) y `tasks.md` (7 grupos, 18 tareas); `openspec validate --strict` → válido.
- **Archivos modificados:** `openspec/changes/add-user-registration/*` (4 artefactos), `tiempos.md` (T-007).
- **Resultado:** planning completo y validado; se frenó en la frontera de openspec.
- **Estado:** Completado.
- **Verificaciones:** `openspec validate add-user-registration --strict` → valid; `openspec status` → 4/4.

## 2026-10-09 13:10 — CU-01: apply (implementación)

- **Contexto / tarea:** CU-01. Implementar el cambio aprobado (backend → frontend → tests → smoke).
- **Prompt utilizado:** "Validado, arranca" (apply).
- **Resumen de la respuesta:** subagente `backend`: scaffolding Flask por capas, modelo `User` (email único, rol enum, hash Werkzeug), `register_user()`, `POST /api/auth/register` y 21 tests (instalación sin fallos de wheels en Python 3.14.6; `pytest -q` 21 passed). El orquestador pasó los mensajes de error de la API a español. Subagente `frontend`: scaffold Vite 7 + React 19, `client.js`, `registerUser()` y `RegisterForm` (build OK). Smoke end-to-end por proxy: alta 201 + duplicado 409.
- **Archivos modificados:** `backend/` (requirements, app, config, models, services, blueprints, tests), `frontend/` (package.json, vite.config, index.html, src/*), `.gitignore` (+`.pytest_cache/`), `AGENTS.md`, `README.md`, `decisiones.md` (D-010), `progreso.md`.
- **Resultado:** CU-01 implementado end-to-end; pendiente `run-verification`, `reviewer` y archivo.
- **Estado:** En progreso.
- **Verificaciones:** `pytest -q` 21 passed; `npm run build` OK; smoke HTTP directo y vía proxy (201/409).

## 2026-10-09 13:28 — CU-01: verificación final, revisión y archivo

- **Contexto / tarea:** CU-01. Cerrar el ciclo: `run-verification`, gate de `reviewer` y archive del cambio.
- **Prompt utilizado:** "arranca" (continuación del apply) + confirmación del usuario de aceptar la revisión inline ante la falla del subagente `reviewer`.
- **Resumen de la respuesta:** verificación final (pytest 21 passed, `npm run build` OK, smoke ya corrido 201/409). El subagente `reviewer` falló al arrancar x2 (`OpenCode's free tier can only be used from within OpenCode`); se hizo revisión inline contra el checklist del reviewer sin bloqueantes (APROBADO) y el usuario aceptó archivarla. `openspec archive add-user-registration --yes` → archivado como `2026-10-09-add-user-registration` con sincronización de specs (4 requirements); `openspec validate --specs --strict` → 1 passed.
- **Archivos modificados:** `errores.md` (entrada falla `reviewer`), `openspec/changes/add-user-registration/tasks.md` (18/18 [x]), `openspec/specs/user-auth/spec.md` (main spec creada), `progreso.md` (CU-01 Completada), `prompts_log.md`, `tiempos.md` (T-009).
- **Resultado:** CU-01 declarado **Completada**; cambio archivado; docs y registros cerrados.
- **Estado:** Completado.
- **Verificaciones:** pytest 21 passed; `npm run build` OK; `openspec validate --specs --strict` OK; `openspec status` → 18/18 tasks.

## 2026-10-09 13:46 — CU-02: planning (openspec propose)

- **Contexto / tarea:** CU-02 (Autenticarse). Generar el cambio `add-user-auth` con los 4 artefactos de planning (proposal, specs, design, tasks), tras definir el mecanismo de sesión (cookie Flask, D-011) y commits de CU-01.
- **Prompt utilizado:** "Arranca" (plan aprobado: fix engram + commits CU-01 + CU-02). Mecanismo de sesión elegido por el usuario: "Cookie de sesión Flask (Recomendado)".
- **Resumen de la respuesta:** se aplicó el fix de engram (`engram init "tp 2"`, `mem_save` escribiendo de nuevo) y se commitearon CU-01 en 5 unidades + gitignore. Luego se creó el cambio `add-user-auth`: proposal, delta `specs/user-auth/spec.md` (5 requirements ADDED: autenticación de credenciales, sesión persistente, consulta de sesión, cierre de sesión), design (D-A..D-G; A2 recuperación de contraseña fuera de alcance; CSRF diferido) y tasks (7 grupos, 16 tareas); `openspec validate add-user-auth --strict` → valid; `openspec status` → 4/4.
- **Archivos modificados:** `.engram/config.json` (fix), `openspec/changes/add-user-auth/*` (4 artefactos), `tiempos.md` (T-010).
- **Resultado:** planning completo y validado; se frenó en la frontera de openspec (D-011 en `decisiones.md` pendiente de registrar en apply).
- **Estado:** Completado.
- **Verificaciones:** `openspec validate add-user-auth --strict` → valid; `openspec status` → 4/4.

## 2026-10-10 08:19 — CU-02: cierre (smoke definitivo, revisión y archive)

- **Contexto / tarea:** CU-02. Cerrar el ciclo completo (tasks 6.1 → 7.3): smoke e2e HTTP + UI con Playwright y soluciones anti-"trabas".
- **Prompt utilizado:** "Hace el smoke de cierre de CU-02 con HTTP clásico + UI con Playwright y las soluciones para que no vuelva a trabarse" (tras aprobar el plan de cierre).
- **Resumen de la respuesta:** se creó `scripts/verify_cu02.py` (wrapper portable: pre-condición de puertos libres, readiness con timeout, smoke contra el proxy `:5173`, cleanup del árbol de procesos; modos `--keep`/`--cleanup`). Smoke HTTP → `Smoke CU-02: 10/10 PASS`, exit 0, sin huérfanos. Smoke de UI con Playwright MCP: registro en la UI → login → header con `Nombre Apellido (email) — Estudiante` → logout → error del backend renderizado; 4 screenshots en `evidencias/cu-02/`; console sin errores inesperados. `tasks.md` 6.1 y 6.2 `[x]`. Docs: AGENTS (tabla API 4 endpoints + smoke CU-02 + MCP playwright + roadmap), README (API, testing, MCP, características, roadmap), `decisiones.md` D-011, `progreso.md`, `errores.md` (huérfanos/duplicados y cierre del punto de freeze). Revisión: el subagente `reviewer` volvió a fallar por tier (mismo error); revisión inline del checklist sin bloqueantes → APROBADO. `openspec archive add-user-auth --yes` → archivado como `2026-10-10-add-user-auth`; `openspec validate --specs --strict` → 1 passed. Commits por unidad de trabajo (6).
- **Archivos modificados:** `scripts/verify_cu02.py`, `scripts/smoke_cu02.py`, `evidencias/cu-02/*.png`, `openspec/specs/user-auth/spec.md`, `openspec/changes/archive/2026-10-10-add-user-auth/`, `AGENTS.md`, `README.md`, `decisiones.md`, `errores.md`, `progreso.md`, `prompts_log.md`, `tiempos.md`, `.gitignore`.
- **Resultado:** CU-02 cerrado y Completada; cambio archivado; evidencia visual verificable.
- **Estado:** Completado.
- **Verificaciones:** `verify_cu02.py` → 10/10 PASS exit 0 (x2 corridas); `--cleanup` → 0 servicios vivos, puertos libres; smoke UI con screenshots; `openspec validate --specs --strict` → 1 passed; `git status` limpio al final.

## 2026-10-10 10:26 — CU-03: planning + apply + verificación

- **Contexto / tarea:** CU-03 (Gestionar cursos). Ciclo spec-driven completo orquestado por `new-use-case`.
- **Prompt utilizado:** "Arrancá CU-03 con new-use-case" (plan aprobado: backend → rutas por rol → seed del admin → frontend con ruteo → tests → smoke → evidencia → docs).
- **Resumen de la respuesta:** cambio `add-course-management` (proposal, delta `specs/course-management/spec.md`, design D-A..D-G, tasks 5 grupos/16 tareas) validado (`openspec validate --strict` → valid, 4/4). Decisiones de diseño acordadas con el usuario: seed silencioso e idempotente, `CAMPUS_ADMIN_EMAIL`/`CAMPUS_ADMIN_PASSWORD` obligatorias, 4 cursos demo (activos e inactivos), `name`/`code` obligatorios con `code` único case-insensitive, asignación de profesor para CU-04, tabla de inscripciones para CU-05, baja lógica con reactivación, listado incluye inactivos, errores 400/403/404/409, ruteo con `react-router-dom`. Backend: modelo `Course`, `course_service` (validaciones en `services/`), blueprint `courses` (5 endpoints con `@login_required`+`@require_roles(UserRole.ADMIN)`), `seed_admin.py` portable. Frontend: `client.js` con `put`/`patch`, `features/courses` (api, `CoursesPage`, `CourseForm`), `App.jsx` con `BrowserRouter` y `ProtectedRoute`. Tests: `test_courses.py` (19) + `test_seed_admin.py` (4) → 55 passed.
- **Archivos modificados:** `openspec/changes/add-course-management/*`, `backend/models/course.py`, `backend/services/course_service.py`, `backend/services/errors.py`, `backend/blueprints/courses.py`, `backend/app.py`, `backend/tests/test_courses.py`, `backend/tests/test_seed_admin.py`, `backend/tests/conftest.py`, `scripts/seed_admin.py`, `scripts/smoke_cu03.py`, `scripts/verify.py`, `frontend/src/api/client.js`, `frontend/src/App.jsx`, `frontend/src/features/courses/*`, `frontend/package.json`, `evidencias/cu-03/*.png`, `decisiones.md` (D-017, D-018), `AGENTS.md`, `README.md`, `progreso.md`, `tiempos.md`, docs.
- **Resultado:** CU-03 implementado y verificado; cierre (revisión, archive, commits) en curso.
- **Estado:** En progreso.
- **Verificaciones:** `pytest` 55 passed; `ruff check`/`format --check` OK; Prettier OK; `npm run build` OK; `scripts/verify.py --cu cu03` → `13/13 PASS` (regresión `--cu cu02` → 10/10 PASS); evidencia UI Playwright (7 screenshots en `evidencias/cu-03/`, consola con solo favicon 404 y 401/403/409 esperados).

## 2026-10-11 12:51 — Design system de frontend: planning + apply + verificación

- **Contexto / tarea:** infraestructura transversal previa a CU-04. Definir y aplicar un design system de frontend reutilizable por los CUs con UI (temas claro/oscuro, color por rol, componentes, shell), en un ciclo spec-driven propio (`add-frontend-design-system`) y con tooling para agentes.
- **Prompt utilizado:** respuestas a las decisiones de diseño: "Bootstrap npm + tokens propios", "color por rol", "motion para animaciones", "estructura src/theme + src/ui + shell src/app", "deps vía npm (no CDN)", "acepto las 4 recomendaciones" (las decisiones D-019/D-020 quedaron acordadas con el usuario antes del apply).
- **Resumen de la respuesta:** cambio `add-frontend-design-system` (proposal, delta `specs/frontend-design-system/spec.md`, design D-A..D-H, tasks con fix de numeración) validado (`openspec validate --strict`). Tooling: nueva skill `.opencode/skills/design-system/SKILL.md`; actualización de agentes `frontend`/`reviewer` y skills `run-verification`/`create-crud`/`new-use-case`; registro en `.atl/skill-registry.md`. Apply: deps npm (`bootstrap`, `bootstrap-icons`, `motion`, `@fontsource/plus-jakarta-sans`); `src/theme/tokens.css` + `ThemeProvider` (data-bs-theme, localStorage `campus-theme`, prefers-color-scheme, anti-flash) + `main.jsx`/`index.html`; `src/ui/*` (Button, Card, Badge, RoleBadge, PageHeader, Spinner, EmptyState, DataTable, FormField, Modal, ConfirmDialog, Toast+Provider, roles, design-system.css, index.js); shell `src/app/*` (AppLayout con transición `motion`, Navbar con chip de rol y toggle, Sidebar por rol, ProtectedRoute, HomePage); migración de `LoginForm`/`RegisterForm`/`CoursesPage`/`CourseForm` al design system; favicon.svg.
- **Archivos modificados:** `openspec/changes/add-frontend-design-system/*`, `frontend/package.json`, `frontend/index.html`, `frontend/public/favicon.svg`, `frontend/src/main.jsx`, `frontend/src/App.jsx`, `frontend/src/theme/*`, `frontend/src/ui/*`, `frontend/src/app/*`, `frontend/src/features/auth/*`, `frontend/src/features/courses/*`, `evidencias/design-system/*.png`, `.opencode/skills/design-system/SKILL.md`, `.opencode/agents/frontend.md`, `.opencode/agents/reviewer.md`, `.opencode/skills/{run-verification,create-crud,new-use-case}/SKILL.md`, `.atl/skill-registry.md`, `decisiones.md` (D-019, D-020), `progreso.md`, `tiempos.md`.
- **Resultado:** design system implementado y verificado; revisión y archivo del cambio pendientes.
- **Estado:** En progreso.
- **Verificaciones:** `npm run build` OK; `npm run lint:format` OK; smoke HTTP CU-03 `13/13 PASS` sin regresiones (`scripts/verify.py --cu cu03 --keep`); evidencia UI Playwright claro/oscuro (login, shell+tabla, modal, confirmación, toast) en `evidencias/design-system/`; consola sin errores inesperados (solo 401 esperado de `GET /api/auth/me` sin sesión).