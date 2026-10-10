# Registro de decisiones

Decisiones técnicas y arquitectónicas relevantes del proyecto. Evita decisiones contradictorias a futuro.

Formato:

- **ID:** identificador incremental.
- **Fecha:** `YYYY-MM-DD`.
- **Decisión:** qué se decidió.
- **Contexto / problema:** situación que la motivó.
- **Alternativas consideradas:** opciones evaluadas.
- **Criterios:** por qué se eligió.
- **Consecuencias / impacto:** efecto a corto y largo plazo.
- **Estado:** Vigente / Superada.

---

## D-001 — Stack tecnológico

- **Fecha:** 2026-10-09.
- **Decisión:** usar el stack definido en la consigna del TP: backend Python 3.14.6 + Flask, frontend React + Vite (Node v24.19.0), base SQLite con SQLAlchemy, chatbot LangChain + Ollama local.
- **Contexto / problema:** el TP define el stack; no hay libertad para reemplazarlo.
- **Alternativas consideradas:** ninguna (stack impuesto por la cátedra).
- **Criterios:** cumplimiento de la consigna.
- **Consecuencias / impacto:** las versiones exactas de librerías quedan PENDIENTE DE DEFINIR y no se cambian sin autorización.
- **Estado:** Vigente.

## D-002 — Arquitectura del backend: capas + Blueprints por dominio

- **Fecha:** 2026-10-09.
- **Decisión:** Flask con Blueprints por dominio (auth, courses, users, tasks, enrollments, grades) y separación en capas `routes → services → models`.
- **Contexto / problema:** 10 casos de uso con varios roles; se necesita una separación de responsabilidades clara para que los agentes no mezclen lógica de negocio con presentación ni con persistencia.
- **Alternativas consideradas:** (a) MVC simple de Flask (menos carpetas, se ensucia con 10 CU); (b) Clean/Hexagonal (máximo desacople, pero excesiva ceremonia para el tamaño del TP).
- **Criterios:** claridad, testeabilidad, bajo boilerplate, idoneidad para 10 CU.
- **Consecuencias / impacto:** la lógica de negocio vive en `services/`; el acceso a datos solo desde `services/` a través de los modelos; validaciones en `services/`.
- **Estado:** Vigente.

## D-003 — Servidores MCP

- **Fecha:** 2026-10-09.
- **Decisión:** usar tres servidores MCP: `engram` (memoria persistente, local), `context7` (documentación, remoto/externo) y `@modelcontextprotocol/server-filesystem` (filesystem, externo, acotado a la carpeta del proyecto). El terminal se resuelve con las herramientas nativas de opencode.
- **Contexto / problema:** el TP exige al menos 2 servidores MCP, al menos 1 externo, integrados en el flujo. Además se busca gestión de contexto de largo plazo y documentación actualizada.
- **Alternativas consideradas:** (a) solo engram + context7 (ya cumple el mínimo, menos config); (b) agregar el server-memory oficial (knowledge graph puro) además de engram; (c) agregar un MCP de terminal comunitario.
- **Criterios:** cubrir las tres categorías pedidas (memoria, filesystem/terminal, documentación), reforzar el criterio MCP del TP, evitar redundancia y riesgo.
- **Consecuencias / impacto:** opencode ya trae filesystem/terminal nativo, por lo que el MCP de filesystem es redundante en capacidades y su valor es demostrativo (sandbox con allowlist). No se usa MCP de terminal (no hay server oficial maduro). Los MCP se declaran en `opencode.json` de proyecto (Fase 2) y se documentan en el README.
- **Estado:** Vigente.

## D-004 — Medición de tiempos

- **Fecha:** 2026-10-09.
- **Decisión:** registrar los tiempos en `tiempos.md` por unidad de trabajo (wall-clock), con categorías (decisión, diseño, implementación, test, documentación, configuración, revisión) y totales acumulados.
- **Contexto / problema:** se requiere medir el tiempo total de desarrollo y desglosarlo (código, decisiones, etc.).
- **Alternativas consideradas:** (a) plugin de opencode para medir por tool-call (instrumentación automática, más precisa pero más trabajo); (b) medición manual por límites de unidad.
- **Criterios:** simplicidad, verificabilidad, disponibilidad inmediata.
- **Consecuencias / impacto:** la medición no separa con precisión "pensar" de "escribir"; queda registrado como mejora futura un plugin de instrumentación.
- **Estado:** Vigente.

## D-005 — Estrategia spec-driven y openspec

- **Fecha:** 2026-10-09.
- **Decisión:** adoptar openspec como herramienta spec-driven, a inicializar antes de comenzar la implementación de CU-01 (tras la aprobación docente de los casos de uso).
- **Contexto / problema:** se planea gestión spec-driven y hay solapamiento entre openspec y el flujo `sdd-*` disponible en el entorno.
- **Alternativas consideradas:** (a) usar el flujo `sdd-*` de gentle-ai; (b) usar openspec.
- **Criterios:** una única fuente de verdad para las specs.
- **Consecuencias / impacto:** no se corren openspec y `sdd-*` simultáneamente. `casos_de_uso.md` es la fuente de verdad actual hasta la migración. **Superada por D-009**: al investigar el entorno se confirmó que el flujo `sdd-*` es la convención openspec (los mismos artefactos en `openspec/`), no un sistema competidor.
- **Estado:** Superada.

## D-006 — Forma del comando del MCP filesystem en Windows

- **Fecha:** 2026-10-09.
- **Decisión:** invocar el MCP `filesystem` con `["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "<ruta del proyecto>"]` y usar forward-slashes en la ruta.
- **Contexto / problema:** un spawn directo de `npx` (sin shell) falla con `ENOENT` en Windows; además, la PowerShell del sistema tiene la execution policy que bloquea `npx.ps1`/`npm.ps1`.
- **Alternativas consideradas:** (a) `["npx", "-y", ...]` (forma documentada, no resuelve en Windows sin `.cmd`); (b) ruta absoluta con backslashes (requiere escapes en JSON).
- **Criterios:** arranque garantizado en Windows, JSON limpio.
- **Consecuencias / impacto:** el comando es específico de Windows (no portable a Linux/macOS) y la ruta del proyecto es específica de esta máquina. Verificado: el server arranca y responde `Secure MCP Filesystem Server running on stdio`.
- **Estado:** Vigente.

## D-007 — Set de subagentes y skills del proyecto

- **Fecha:** 2026-10-09.
- **Decisión:** crear 5 subagentes (`backend`, `frontend`, `database`, `tester`, `reviewer` read-only) y 5 skills (`track-time`, `new-use-case`, `create-crud`, `create-migration`, `run-verification`).
- **Contexto / problema:** el TP pide roles especializados y skills reutilizables, pero advierte no crear por cumplir una lista.
- **Alternativas consideradas:** (a) los 6 subagentes de la plantilla (incluye `architect`); (b) crear skills por cada patrón visible (se descartaron `create-react-page`, `log-decision` y `generate-docs` por estar absorbidos por `create-crud`/`new-use-case`/las subagentes); (c) este set mínimo.
- **Criterios:** que cada skill resuelva una tarea concreta y repetitiva sin duplicarse; que cada subagente tenga una responsabilidad no solapada; el `architect` se omite porque el diseño de contrato ya está en `casos_de_uso.md` + `AGENTS.md`.
- **Consecuencias / impacto:** el flujo por CU queda orquestado por `new-use-case`, que delega al resto; `reviewer` es obligatorio antes de marcar un CU como Completo. Si un patrón se repite, se recomienda una skill nueva.
- **Estado:** Vigente.

## D-008 — Repositorio GitHub

- **Fecha:** 2026-10-09.
- **Decisión:** publicar el proyecto en GitHub en el repo **público** `https://github.com/Franco2900/campus-virtual` (dueño: Franco2900), rama `main`, con `gh` autenticado por HTTPS y commits por unidad de trabajo.
- **Contexto / problema:** la consigna pide repositorio con README exhaustivo como bitácora; el repo público comparte la evidencia del proceso de AI Engineering.
- **Alternativas consideradas:** (a) repo privado; (b) nombre con prefijo `tp2-`; (c) este repo público `campus-virtual`.
- **Criterios:** visibilidad de la bitácora para la evaluación; nombre corto y descriptivo.
- **Consecuencias / impacto:** el material fuente de la cátedra (`Consignas TP.txt`, `Casos de uso.txt`, `Plantilla para proyecto con IA/`) queda público junto con el resto; si en algún momento se prefiere retirarlo, se quita del tracking con `git rm --cached`. `.atl/` no se publica (`.gitignore`).
- **Estado:** Vigente.

## D-009 — Operación de openspec en la Fase 6

- **Fecha:** 2026-10-09.
- **Decisión:** inicializar openspec con el CLI oficial (`openspec init --tools opencode --language es --force --no-copilot-cloud`, v1.13.2) y operar cada caso de uso con el pipeline spec-driven orquestado por la skill `new-use-case` (propose → specs → design → tasks → apply → verify → archive), delegando la implementación a los subagentes del proyecto. Las skills `openspec-*` y comandos `/opsx-*` generados por el CLI quedan como vía nativa alternativa.
- **Contexto / problema:** el OK docente desbloquea la Fase 6; D-005 fijó openspec y descartó (erróneamente) el flujo `sdd-*` como competidor. La investigación mostró que `sdd-*` es openspec (misma convención de artefactos en `openspec/`).
- **Alternativas consideradas:** (a) solo CLI openspec para todo el ciclo; (b) pipeline `sdd-*` sobre el bootstrap del CLI (elegida); (c) descartar las skills/commands autogenerados por el CLI.
- **Criterios:** una única fuente de verdad (`openspec/`), máxima trazabilidad de AI Engineering (foco de la evaluación), menor fricción por CU, no luchar contra el tool.
- **Consecuencias / impacto:** `openspec config.yaml` con `strict_tdd: false` (no hay comando de tests todavía; se habilita cuando exista un runner de workspace). `casos_de_uso.md` sigue como fuente humana de los CU; openspec pasa a ser la fuente de verdad de specs. El `.opencode/.gitignore` autogenerado (oculta `node_modules`/`package.json` de openspec) se respeta.
- **Estado:** Vigente.

## D-010 — Stack y esquema del primer caso de uso (CU-01)

- **Fecha:** 2026-10-09.
- **Decisión:** al implementar CU-01 se fijaron: backend con Flask 3.1.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.54, Werkzeug 3.1.9 (hashing) y pytest 9.1.1 (pinned en `backend/requirements.txt`); frontend con React 19.3.0, Vite 7.3.7 y `@vitejs/plugin-react` 5.2.0 (pinned en `frontend/package.json`); esquema inicial con `db.create_all()` (sin migraciones todavía); CORS resuelto con el proxy de desarrollo de Vite (`/api → http://localhost:5000`, sin `flask-cors`); frontend organizado por feature (`src/features/<feature>/` + `src/api/client.js`); mensajes de error de la API en español (UI orientada a hispanohablantes).
- **Contexto / problema:** CU-01 requiere el scaffolding completo (no había código); había que decidir versiones, hashing, init de esquema, CORS y estructura del frontend.
- **Alternativas consideradas:** (a) `passlib`+`bcrypt` para hashing (descartado: wheel incierto en Python 3.14.6 en Windows; `werkzeug.security` es puro Python y valida en CU-02); (b) Flask-Migrate/Alembic desde el inicio (descartado: no hay esquema ni datos previos); (c) `flask-cors` (descartado: el proxy de Vite lo vuelve innecesario en dev); (d) frontend por tipo con carpetas `components/` (descartado: bolsa de gato a 10 CU).
- **Criterios:** dependencias mínimas, portabilidad, ceremonia proporcional.
- **Consecuencias / impacto:** las versiones quedan pinned y no se cambian sin autorización; las migraciones se introducirán (skill `create-migration`) cuando un CU modifique un esquema con datos. El mecanismo de sesión/token se decide en CU-02 (CU-01 no autentica).
- **Estado:** Vigente.

## D-011 — Mecanismo de sesión: cookie firmada de Flask

- **Fecha:** 2026-10-09.
- **Decisión:** CU-02 autentica con la cookie de sesión firmada del propio Flask (dada por `itsdangerous`): `session["user_id"] = user.id` en login, `logout()` limpia la cookie, y las rutas protegidas usan el decorador `@login_required` de `backend/blueprints/guards.py`. La sesión se inicia en `POST /api/auth/login`, se consulta con `GET /api/auth/me` (requiere sesión) y se cierra con `POST /api/auth/logout` (idempotente).
- **Contexto / problema:** CU-01 dejó diferido el mecanismo de sesión/token; CU-02 lo exige para los 10 CU siguientes.
- **Alternativas consideradas:** (a) JWT en `localStorage`/header `Authorization` (stateless, pero expone el token a XSS y agrega manejo de expiración/refresh); (b) Flask-Session con almacenamiento server-side (sesiones revocables, pero agrega dependencia y almacenamiento inútil para una sola instancia); (c) cookie de sesión firmada de Flask (elegida).
- **Criterios:** seguridad básica suficiente (cookie `HttpOnly` + `SameSite=Lax` prefijadas por Flask evita exfiltración por XSS; el token nunca llega a JavaScript), cero dependencias nuevas, simplicidad para 10 CU, portabilidad.
- **Consecuencias / impacto:** la cookie es la única fuente de verdad de la sesión; `Session` en el cliente (`frontend/src/features/auth/api.js`) guarda solo estado de UI y el `me` revalida contra el servidor; las rutas de CU-03 en adelante se protegen con `@login_required` (y chequearán rol vía `current_user`).
- **Estado:** Vigente.

## D-012 — MCP Playwright para verificación e2e de UI

- **Fecha:** 2026-10-09.
- **Decisión:** agregar el MCP local `playwright` (`@playwright/mcp@latest`, headless + chromium) a `opencode.json` para validar la UI real durante el ciclo de cada CU. Complementa (no reemplaza) a `run-verification` (pytest/build/smoke HTTP): se usa de forma interactiva para navegar, completar formularios y capturar screenshots como evidencia verificable. Comando con prefijo `cmd /c` por la execution policy de Windows (mismo patrón que D-006).
- **Contexto / problema:** el smoke HTTP valida backend + proxy + cookie (CU-01 y CU-02) pero no la UI real (interacción con formularios, navegación, mensajes renderizados). Desde CU-03 los CRUD por rol tienen pantallas cuya corrección visual es parte de la funcionalidad evaluada.
- **Alternativas consideradas:** (a) Playwright MCP headless (elegida); (b) headed (mejor para debug humano, requiere display; la evidencia se produce igual con screenshots); (c) suite de tests Playwright por código (más robusto para CI, pero agrega escritura de tests permanente fuera del alcance del TP); (d) no agregar nada (se pierde validación visual).
- **Criterios:** evidencia verificable (screenshots), cero dependencias nuevas en la app (se ejecuta vía `npx`, no entra a `requirements.txt`/`package.json`), portabilidad del código de la app intacta.
- **Consecuencias / impacto:** el MCP se carga al reiniciar opencode; la primera ejecución puede requerir instalar el browser (`npx playwright install chromium`). Es tooling de la máquina, no parte del sistema portable. No sustituye a pytest ni al smoke HTTP: los tres conviven (tests → lógica, smoke → cadena HTTP, Playwright → UI).
- **Estado:** Vigente.

## D-013 — Plugin opencode-notification para avisos de escritorio

- **Fecha:** 2026-10-09.
- **Decisión:** instalar el plugin `opencode-notification` (npm, `plugin: ["opencode-notification@latest"]`) en `opencode.json` para notificaciones de escritorio cuando la sesión termina, pide permiso, falla o lanza una pregunta. En Windows usa toasts de PowerShell; defaults low-noise (delay 15 s).
- **Contexto / problema:** el usuario pidió avisos de escritorio para no quedarse mirando el terminal durante tareas largas. El candidato inicial `opencode-notificator` (panta82) declara soporte macOS/Linux sin confirmar Windows.
- **Alternativas consideradas:** (a) `opencode-notification` (elegida: Windows confirmado vía PowerShell toast, bajo ruido por defecto); (b) `@xtccc/opencode-notifier` (Windows out of the box, más eventos, más config); (c) `opencode-notificator` (sin Windows confirmado); (d) plugin propio con el hook `event` (más código a mantener).
- **Criterios:** soporte Windows, bajo ruido, cero dependencias en la app.
- **Consecuencias / impacto:** los avisos llegan cuando el terminal no está enfocado (por defecto); se activa al reiniciar opencode. Config opcional vía `oc-notification.json` (delay y eventos por tipo). No es un MCP (no agrega herramientas), solo notificaciones.
- **Estado:** Vigente.

## D-014 — Evidencia y revisión obligatorias por CU

- **Fecha:** 2026-10-10.
- **Decisión:** todo CU se cierra con (a) evidencia verificable: screenshots estandarizados en `evidencias/cu-0X/` (`NN-accion.png`, full-page cuando aporte) que muestren los estados clave por rol y consola sin errores inesperados, o salida real de smoke/tests si el CU no es visual; y (b) un artefacto de revisión `reviews/cu-0X.md` persistido con hallazgos (`archivo:línea`, severidad Bloqueante/Alta/Media/Baja), veredicto APROBADO/RECHAZADO y mapa de evidencia. La revisión corre con el subagente `reviewer`; si no está disponible por error de tier del proveedor (ocurrió en CU-01 y CU-02), se ejecuta inline con la skill `review-use-case`.
- **Contexto / problema:** la revisión y la evidencia vivían solo en el chat de la sesión y la cátedra evalúa la orquestación de AI Engineering; sin artefactos persistidos no hay trazabilidad ni gate objetivo.
- **Alternativas consideradas:** (a) checklist inline sin artefacto (elegida antes, sin dejar rastro); (b) veredicto en `progreso.md` (sin mapa de evidencia); (c) artefacto dedicado por CU (elegida).
- **Criterios:** trazabilidad evaluable, gate verificable, repetible cuando el subagente falla, mínimo esfuerzo por CU.
- **Consecuencias / impacto:** el pipeline `new-use-case` incorpora el paso de evidencia y revisión antes del archive; AGENTS documenta la sección "Evidencia y revisiones".
- **Estado:** Vigente.

## D-015 — Lint y formato automáticos (ruff + Prettier)

- **Fecha:** 2026-10-10.
- **Decisión:** adoptar `ruff` (Python, `==0.16.9` en `backend/requirements.txt`) y `Prettier` (JS/JSX, devDependency del frontend) con config mínima (`backend/pyproject.toml`: line-length 100, target py314; `frontend/.prettierrc`: printWidth 100, semis, comillas dobles). Comandos: `python -m ruff check backend` / `python -m ruff format --check backend`; `npm run lint:format` / `lint:format:fix`. Se formateó todo el código existente en un único commit de estilo.
- **Contexto / problema:** era la "PENDIENTE DE DEFINIR" más antigua de AGENTS; sin formateador se acumulaba deuda de estilo y los diffs mezclaban formato con lógica.
- **Alternativas consideradas:** (a) Black (solo Python, sin lint); (b) ruff + Prettier (elegida: ruff = lint + format en una herramienta; Prettier estándar para React); (c) flake8 + black (dos herramientas por filetype, más config).
- **Criterios:** una herramienta por lenguaje, cero plugins de editor, chequeos ejecutables en CI, no tocar la lógica.
- **Consecuencias / impacto:** el CI agrega jobs de lint/format (Fase U4); los agentes usan `ruff format`/`prettier` antes de cerrar unidades; las convenciones de "Indentación / formato" quedan definidas.
- **Estado:** Vigente.

## D-016 — CI con GitHub Actions (tests + build + lint)

- **Fecha:** 2026-10-10.
- **Decisión:** agregar `.github/workflows/ci.yml` en `ubuntu-latest` con tres jobs que corren en cada push y PR a `main`: `test` (Python 3.14, `pytest` en `backend/`), `build` (Node 24, `npm ci` + `npm run build` en `frontend/`) y `lint` (`ruff check` + `ruff format --check` + `prettier --check`).
- **Contexto / problema:** se detectaron regresiones tarde (test que rompió un cambio de UI) y no había señal temprana; el TP gana credibilidad con verificación continua.
- **Alternativas consideradas:** (a) CI en GitHub Actions (elegida: el repo ya vive en GitHub y es gratuito para repos públicos); (b) Git hooks locales (solo cubren a quien los instale); (c) no hacer nada.
- **Criterios:** cero costo, portabilidad (valida la CROSS-platform que ya se garantiza en código), sin dependencias nuevas.
- **Consecuencias / impacto:** cualquier push se valida solo; los tests y el build ya pasan en local, el primer run de CI lo confirma; no se toca el stack.
- **Estado:** Vigente.

## D-017 — Bootstrap del Administrador inicial vía seed con variables de entorno

- **Fecha:** 2026-10-10.
- **Decisión:** el primer usuario Administrador se crea con un script portable `scripts/seed_admin.py` que lee `CAMPUS_ADMIN_EMAIL` y `CAMPUS_ADMIN_PASSWORD` (ambas obligatorias; si faltan, falla con mensaje claro) y crea el admin (`role=ADMIN`) más 4 cursos de demostración (activos e inactivos). El script es idempotente: si el admin ya existe, no duplica ni re-siembra cursos. Para el smoke, `scripts/verify.py` lo ejecuta contra una base SQLite temporal aislada (`CAMPUS_DB_PATH` en un directorio `tempfile`) y propaga esas credenciales al smoke.
- **Contexto / problema:** CU-01 fuerza el rol Estudiante en el registro y la asignación de roles es CU-04; ninguna vía de la API puede crear un Administrador, por lo que CU-03 (gestión de cursos, sólo Administrador) quedaba sin forma de autenticarse para probarse. No se puede hardcodear un secreto.
- **Alternativas consideradas:** (a) permitir un rol en el registro (rompe la regla de rol forzado de CU-01); (b) crear el admin "a mano" en la base (no reproducible ni portable); (c) endpoint de bootstrap protegido por token (superficie de ataque extra); (d) script de seed con variables de entorno (elegida).
- **Criterios:** reproducible, portable (Windows/Linux/macOS), sin secretos en el repo, idempotente, sin ampliar la superficie de la API pública.
- **Consecuencias / impacto:** para correr el sistema hace falta definir las dos variables de entorno antes del seed; el seed crea también datos de demo (4 cursos) útiles para los CU siguientes. La asignación de Profesor y la relación profesor↔curso quedan para CU-04 (no se mezclan acá).
- **Estado:** Vigente.

## D-018 — Ruteo del frontend con react-router-dom

- **Fecha:** 2026-10-10.
- **Decisión:** introducir `react-router-dom` en el frontend y organizar la navegación con `BrowserRouter`: rutas `/login`, `/register` y `/courses` (protegida por rol Administrador), más `/` que redirige según el rol. La sesión se restaura al montar con `getMe()`; una ruta `ProtectedRoute` muestra "Cargando...", redirige a `/login` si no hay sesión y bloquea por rol si no coincide. El registro **no** inicia sesión en el cliente (el backend no emite cookie en `POST /api/auth/register`): tras registrarse se navega a `/login`.
- **Contexto / problema:** hasta CU-02 la app renderizaba por condición con un toggle local (`showLogin`); con múltiples pantallas por rol eso no escala ni da URLs navegables. Además se detectó (vía evidencia Playwright) que asumir sesión tras el registro mostraba la UI logueada sin cookie, expulsando al usuario al recargar.
- **Alternativas consideradas:** (a) seguir con render condicional (no escala); (b) router completo como TanStack Router (más potente, más ceremonia); (c) `react-router-dom` (elegida: estándar, diffs chicos, cubre guard por rol).
- **Criterios:** URLs navegables, guard de sesión/rol en un solo lugar, dependencia estándar y liviana, cambio incremental sobre `App.jsx`.
- **Consecuencias / impacto:** el servidor de dev de Vite debe servir el fallback de SPA (ya lo hace por defecto); las próximas pantallas se agregan como features con su ruta y su guard. El registro queda como acción previa al login (coherente con que la cookie sólo se emite en login).
- **Estado:** Vigente.
