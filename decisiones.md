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
- **Estado:** Vigente (el punto «esquema inicial con `db.create_all()` / sin migraciones todavía» queda superado por D-023).

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

## D-019 — Design system propio sobre Bootstrap (tokens + tema claro/oscuro)

- **Fecha:** 2026-10-11.
- **Decisión:** el frontend usa `bootstrap` (CSS + API JS) y `bootstrap-icons` como dependencias npm (sin CDN, sin `react-bootstrap`), y una capa propia de design system: tokens CSS en `frontend/src/theme/tokens.css` (marca, colores por rol, semánticos y neutros en claro y oscuro, mapeados a variables de Bootstrap 5.3) y componentes reutilizables en `frontend/src/ui/` (`Button`, `Card`, `Badge`, `RoleBadge`, `DataTable`, `FormField`, `Modal`, `ConfirmDialog`, `Toast`+`ThemeProvider`). El tema se resuelve con `ThemeProvider` (`src/theme/ThemeProvider.jsx`): setea `data-bs-theme` en `<html>`, persiste en `localStorage` (`campus-theme`) y por defecto usa `prefers-color-scheme`; un script inline anti-flash en `index.html` aplica el tema antes del primer render. La estructura del frontend queda `src/app/` (shell: `AppLayout`, `Navbar`, `Sidebar`, `ProtectedRoute`), `src/ui/` (design system) y `src/theme/` (tokens + provider). Tipografía Plus Jakarta Sans vía `@fontsource`.
- **Contexto / problema:** el frontend era HTML sin estilos ni librería de UI; con 10 CU por delante (varios con pantallas) no era viable reescribir estilos en cada uno. Se necesitaba una base visual coherente, accesible, con temas claro/oscuro y color por rol (Estudiante/Profesor/Administrador), sin acoplarse a una librería de componentes React.
- **Alternativas consideradas:** (a) Bootstrap por CDN (rompe el flujo Vite/npm y la portabilidad offline); (b) `react-bootstrap` (capa React extra que no se necesita; más dependencias); (c) Tailwind + componentes propios (reescritura total y más curva); (d) Bootstrap npm + tokens CSS propios + componentes mínimos en `src/ui/` (elegida: control total del look, pocas dependencias, reutilizable por los CUs).
- **Criterios:** reutilización entre CUs, accesibilidad (foco visible, `role`, `prefers-reduced-motion`), temas claro/oscuro sin duplicar CSS, color por rol como tokens, cero colores hardcodeados en pantallas, portabilidad (deps npm, no CDN).
- **Consecuencias / impacto:** cada CU con UI construye sobre `src/ui/` y tokens; el revisor agrega checklist de design system/accesibilidad/temas; la evidencia UI se captura en claro y oscuro. Bootstrap JS se envuelve con refs (`Modal`), no se usa la API imperativa suelta en pantallas.
- **Estado:** Vigente.

## D-020 — Animaciones con `motion` y micro-interacciones CSS

- **Fecha:** 2026-10-11.
- **Decisión:** usar `motion` (paquete npm, import `motion/react`) para animaciones de mayor nivel —transición de página en `AppLayout` y entrada/salida de toasts (`AnimatePresence`)— y CSS del design system para micro-interacciones (hover de nav, transición de tema). Se respeta `prefers-reduced-motion` (override CSS global y `useReducedMotion` en los componentes animados).
- **Contexto / problema:** el frontend no tenía ninguna noción de movimiento; se quería una app que se sintiera viva (transiciones y feedback) sin cargar una librería pesada ni degradar la accesibilidad de quienes piden menos movimiento.
- **Alternativas consideradas:** (a) Framer Motion (predecesor; `motion` es su sucesor más liviano); (b) solo CSS (suficiente para micro-interacciones, pobre para transición de páginas y exit de listas); (c) `motion` (elegida: API declarativa, `AnimatePresence`, respeto nativo de `prefers-reduced-motion`).
- **Criterios:** animaciones declarativas y acotadas, respeto de accesibilidad, dependencia única y liviana, sin JS imperativo de animación en pantallas.
- **Consecuencias / impacto:** las transiciones viven en el shell y en los componentes del design system, no en cada pantalla; los CUs nuevos heredan el comportamiento sin código extra.
- **Estado:** Vigente.

## D-021 — Gestión de usuarios por el Administrador (CU-04)

- **Fecha:** 2026-10-11.
- **Decisión:** el Administrador gestiona las cuentas: listado (incluye inactivas), detalle, edición de datos y rol, activar/desactivar (baja lógica con `User.active`) y reset de contraseña (el Admin fija la nueva). Endpoints `GET /api/users`, `GET /api/users/<id>`, `PUT /api/users/<id>`, `PATCH /api/users/<id>` (body `{"active": <bool>}`), `POST /api/users/<id>/password`, todos con `@login_required` + `@require_roles(UserRole.ADMIN)` (403 por rol). La **autogestión está bloqueada**: el Admin no puede desactivarse ni cambiarse el rol a sí mismo (400 vía `ValidationError`, decisión explícita: es validación de entrada, no de autorización). Una cuenta **inactiva no puede autenticarse** (`authenticate_user` y `get_current_user` la rechazan).
- **Contexto / problema:** CU-04 exige que el Administrador administre las cuentas; hasta ahora sólo el registro público creaba usuarios con rol Estudiante forzado, y no había forma de asignar otros roles ni de dar de baja.
- **Alternativas consideradas:** (a) borrado físico (pierde trazabilidad y rompe referencias); (b) baja lógica con `active` (elegida); (c) reset de contraseña por correo con token y expiración (fuera de alcance: el TP no envía correos); (d) 403 para la autogestión (se prefirió 400).
- **Criterios:** exclusividad de rol, email único case-insensitive, baja lógica reversible, sin notificaciones por correo (regla del TP), validaciones en `services/`, contraseña con longitud mínima.
- **Consecuencias / impacto:** `active` incide en el login y en la sesión vigente; el listado **no** filtra todavía (eso es CU-10); el reset de contraseña no emite correo (el Admin comunica el valor).

## D-022 — Relación Profesor↔curso (tabla asociativa)

- **Fecha:** 2026-10-11.
- **Decisión:** modelar la asignación Profesor↔curso con la tabla asociativa `course_teacher` (`course_id` FK, `teacher_id` FK, `UNIQUE(course_id, teacher_id)`), gestionada por `GET/POST /api/courses/<id>/teachers` y `DELETE /api/courses/<id>/teachers/<teacher_id>` (solo Administrador). Las validaciones viven en `services/course_teacher_service.py`: curso existente (404), `teacher_id` requerido (400), usuario existente (404), rol Profesor (400), duplicado (409). El listado expone id, nombre, apellido, email y rol.
- **Contexto / problema:** la regla de negocio «un Profesor sólo opera sobre los cursos en los que trabaja» (CU-06/07/08) exige persistir la relación; se incorporó en CU-04 por decisión explícita (no estaba en el alcance mínimo del CU, pero desbloquea los CU por rol).
- **Alternativas consideradas:** (a) FK simple `Course.teacher_id` (un curso = un solo profesor; insuficiente); (b) tabla asociativa N:M (elegida); (c) lista JSON dentro de `Course` (sin integridad referencial).
- **Criterios:** relación N:M realista (varios profesores por curso y un profesor en varios cursos), integridad referencial y unicidad garantizadas por la base.
- **Consecuencias / impacto:** los CUs que operan según el profesor (CU-06, CU-07, CU-08) autorizarán consultando esta tabla; la relación se administra sólo por el Administrador.

## D-023 — Migraciones de esquema con Flask-Migrate (Alembic)

- **Fecha:** 2026-10-11.
- **Decisión:** adoptar **Flask-Migrate** (`4.1.0`) con **Alembic** (`1.20.0`) integrado al factory (`Migrate(app, db)`) para evolucionar el esquema con migraciones versionadas en `backend/migrations/`. `db.create_all()` queda limitado a `app.config["TESTING"]`. La base existente se llevó al esquema pre-CU-04 con un **baseline** (`0001_baseline_pre_cu_04`) + `flask db stamp`; los cambios de CU-04 se aplican con migraciones incrementales (`0002` agrega `user.active` con `server_default` para el backfill de filas existentes; `0003` crea `course_teacher`). `scripts/verify.py` y `scripts/seed_admin.py` corren `flask db upgrade` sobre la base (temporal o real) antes de usarla. El código generado de `backend/migrations/` queda **excluido de ruff** (`extend-exclude` en `backend/pyproject.toml`).
- **Contexto / problema:** D-010 y AGENTS dejaban las migraciones para el primer CU que cambiara el esquema con datos; CU-04 agrega `user.active` (NOT NULL) sobre una tabla con filas y una tabla nueva —el primer cambio de esquema con datos—.
- **Alternativas consideradas:** (a) seguir con `db.create_all()` (no agrega columnas nuevas ni hace backfill); (b) SQL manual (no portable ni versionado); (c) Flask-Migrate/Alembic (elegida).
- **Criterios:** versionado del esquema, portabilidad Windows/Linux/macOS, backfill reproducible, tooling estándar de Flask.
- **Consecuencias / impacto:** todo CU que cambie el esquema debe generar una migración (skill `create-migration`); `migrations/` se versiona en git (no se ignora); `db.create_all()` queda sólo para tests; el baseline pre-CU-04 documenta el punto de arranque.
- **Estado:** Vigente.

## D-024 — Modelo de inscripción y semántica de sus operaciones (CU-05)

- **Fecha:** 2026-10-11.
- **Decisión:** modelar la inscripción con la entidad `Enrollment` (`id` PK, `course_id` FK→`course.id`, `student_id` FK→`user.id`, `active` default `True`, `enrolled_at` UTC, `UNIQUE(course_id, student_id)`, migración `0004`). Semántica: **alta** con `POST` (no hace upsert: si ya existe fila —activa o inactiva— responde 409), **modificación** con `PATCH {"active": <bool>}` (activar/desactivar = baja lógica reversible) y **eliminación** con `DELETE` (borrado físico, permitido aunque el curso esté inactivo). Validaciones sólo en `services/enrollment_service.py`, en el orden determinista: 401 guard → 403 rol → 404 curso → 403 Profesor no asignado → 409 curso inactivo (sólo POST/PATCH) → 404 estudiante → 400 cuenta no-estudiante o inactiva → 409 duplicado.
- **Contexto / problema:** CU-05 exige que Admin/Profesor gestionen las inscripciones de estudiantes en cursos; no existía entidad de inscripción. Se necesitaba decidir si "modificar" y "eliminar" eran la misma operación (baja lógica) o distintas, y si la alta era idempotente.
- **Alternativas consideradas:** (a) `POST` con upsert (idempotente; rechazado: oculta el conflicto y complica la distinción alta/reactivación); (b) sólo baja lógica sin borrado físico (pierde la posibilidad de una baja definitiva); (c) alta 409 + `PATCH` para activar/desactivar + `DELETE` físico (elegida).
- **Criterios:** integridad referencial y unicidad por base, conflicto explícito en la alta, separación clara entre baja lógica (reversible) y borrado físico, curso debe estar activo para inscribir/desinscribir.
- **Consecuencias / impacto:** un mismo estudiante puede figurar con inscripción activa o inactiva (lista con `null` si nunca se inscribió); reactivar usa `PATCH`, no `POST`; el borrado físico sólo lo habilita `DELETE`. `Enrollment` debe registrarse en `app.py` y en `tests/test_migrations.py` (paridad modelos↔migraciones).
- **Estado:** Vigente.

## D-025 — Alcance por rol de la gestión de inscripciones y `GET /api/courses/mine`

- **Fecha:** 2026-10-11.
- **Decisión:** los endpoints de inscripciones son subrecursos de curso (`GET/POST /api/courses/<id>/students`, `PATCH/DELETE /api/courses/<id>/students/<student_id>`) en un blueprint nuevo `blueprints/enrollments.py` con `url_prefix="/api/courses"`, con `@login_required` + `@require_roles(UserRole.ADMIN, UserRole.TEACHER)`. El **Administrador** opera sobre cualquier curso; el **Profesor** sólo sobre los cursos en los que está asignado (si no, 403 vía `ForbiddenError`). Se agrega `GET /api/courses/mine` (Admin: todos los cursos; Profesor: los asignados vía `course_teacher`) para que el Profesor elija su curso. `GET /api/courses/<id>/students` lista los estudiantes activos con la inscripción anidada (activa o inactiva) o `null`.
- **Contexto / problema:** la regla de negocio «un Profesor sólo opera sobre los cursos en los que trabaja» aplica a CU-05; el Profesor necesita una fuente de cursos acotada a su alcance, y la restricción admin-only previa de `GET /api/courses` (CU-03) lo impedía.
- **Alternativas consideradas:** (a) reusar `GET /api/courses` abierto a Profesor (rompe la restricción admin-only de CU-03); (b) endpoint dedicado `GET /api/courses/mine` (elegida: mantiene `GET /api/courses` admin-only y expresa "mis cursos"); (c) endpoints de inscripción dentro de `courses.py` (mezcla dominios).
- **Criterios:** respeto de la restricción admin-only de CU-03, alcance por rol explícito, coherencia con el patrón de subrecurso `/teachers`, blueprint por dominio (D-002).
- **Consecuencias / impacto:** la spec `course-management` se modifica para acotar la restricción admin-only exceptuando `GET /api/courses/mine`; la autorización del Profesor se resuelve consultando `course_teacher`; los CU que operen por profesor (CU-06/07/08) pueden reusar `list_courses_for_user`/`/mine`.
- **Estado:** Vigente.

## D-026 — Modelo de tarea y su semántica (CU-06)

- **Fecha:** 2026-10-13.
- **Decisión:** modelar la tarea con la entidad `Task` (`id` PK, `course_id` FK→`course.id`, `title` obligatorio no vacío ≤200, `description` opcional default `""` ≤1000, `due_date` obligatoria ISO 8601, `active` default `True`, `created_at` UTC, migración `0005_add_task`). Semántica: **alta** con `POST` (siempre activa, asociada al curso), **modificación** con `PUT` (incluye la fecha límite, flujo alternativo A1) y **activación/desactivación** con `PATCH {"active": <bool>}` (baja lógica reversible; una tarea inactiva no se considera disponible para los estudiantes). La `due_date` debe estar presente y ser parseable (se tolera el sufijo `Z`), pero **no** se exige que sea futura: la vigencia del plazo se resuelve en CU-07.
- **Contexto / problema:** CU-06 exige que el Profesor cree, consulte, modifique y desactive tareas; no existía ninguna entidad de tarea, base necesaria para CU-07 (entrega), CU-08 (corrección) y CU-09 (calificaciones).
- **Alternativas consideradas:** (a) exigir fecha futura ya en CU-06 (rechazado: sobre-construye una regla que el propio CU delega a la entrega e impide ajustes legítimos de fecha en A1); (b) modelar "desactivar" como borrado físico (rechazado: el CU dice "cambia el estado a inactivo", es baja lógica).
- **Criterios:** fidelidad a `casos_de_uso.md`, disponibilidad de la tarea para el Estudiante como derivada de `active` + `due_date`, versionado de esquema (D-023).
- **Consecuencias / impacto:** `Task` se registra en `app.py` y en `tests/test_migrations.py` (paridad modelos↔migraciones); CU-07/CU-08 dependen de `Task.active` y `Task.due_date`; la columna `due_date` es `DateTime(timezone=True)` pero SQLite no preserva el offset en el round-trip (limitación conocida, se difiere a CU-07).
- **Estado:** Vigente.

## D-027 — Endpoints anidados de tareas y alcance Profesor-only (CU-06)

- **Fecha:** 2026-10-13.
- **Decisión:** los endpoints de tareas son subrecursos de curso en un blueprint nuevo `blueprints/tasks.py` con `url_prefix="/api/courses"` e `@login_required` + `@require_roles(UserRole.TEACHER)`: `GET/POST /api/courses/<id>/tasks` y `GET/PUT/PATCH /api/courses/<id>/tasks/<task_id>`. Solo el **Profesor** opera (Estudiante y Administrador reciben 403) y únicamente sobre los cursos en los que está asignado (si no, 403). Orden de validaciones determinista (design D-J): 401 → 403 rol → 404 curso inexistente → 403 Profesor no asignado → 409 curso inactivo (solo POST/PUT) → 400 datos → 404 tarea. Se habilita `PATCH` aun con el curso inactivo. `get_manageable_course` se mueve de `enrollment_service` a `course_service` para que `task_service` lo reutilice sin depender del dominio de inscripciones.
- **Contexto / problema:** CU-06 define al Profesor como único actor y la regla «un Profesor solo opera sobre los cursos en los que trabaja»; había que decidir el recorte de autorización y la ubicación del filtro de alcance.
- **Alternativas consideradas:** (a) habilitar también al Administrador (como en CU-05) — rechazado por decisión de alcance acordada con el usuario: fidelidad al CU y menor superficie; (b) duplicar `get_manageable_course` en `task_service` — rechazado por duplicar una regla de negocio; (c) moverla a `course_service` y reutilizarla (elegida).
- **Criterios:** fidelidad a `casos_de_uso.md`, concentración del filtro de alcance por curso (señalado en `reviews/cu-05.md`), coherencia con el patrón de subrecurso de CU-05 y el orden de validaciones ya fijado.
- **Consecuencias / impacto:** el frontend usa `GET /api/courses/mine` para el selector de curso y bloquea crear/modificar en cursos inactivos; el mismo filtro `get_manageable_course` queda listo para CU-08; `enrollment_service` importa `get_manageable_course` desde `course_service` (mismo comportamiento, sin cambios en sus tests).
- **Estado:** Vigente.

## D-028 — Eliminación de la medición de tiempos y la skill `track-time`

- **Fecha:** 2026-10-13.
- **Decisión:** eliminar `tiempos.md` y la skill `track-time` (`.opencode/skills/track-time/`) y dejar de registrar tiempos por unidad de trabajo, por decisión del usuario al optimizar el uso de tokens: calcular el tiempo no es necesario para el proyecto. **Supersede a D-004.** Se limpian todas las referencias activas (tabla de skills en `AGENTS.md`, mapa de archivos en `AGENTS.md`/`README.md`, protocolo de "Fases y sesiones", pasos de `new-use-case` y `.atl/skill-registry.md`); los archivos eliminados siguen recuperables desde git; las entradas históricas (archived openspec, `reviews/`, `errores.md`, `prompts_log.md`) no se reescriben.
- **Contexto / problema:** la medición manual de tiempos consumía varios tool calls por CU y perdía marcas por compactación de contexto (p. ej. T-024 quedó PENDIENTE); el "plugin de medición automática" del roadmap quedaba descartado porque la medición ya no es un requisito.
- **Alternativas consideradas:** (a) automatizar la medición con un plugin de opencode (descartado: sobre-ingeniería para algo que el usuario declaró innecesario); (b) mantener `tiempos.md` sin skill (descartado: la skill era su único mantenimiento y ambas quedan sin consumidores); (c) eliminar ambos (elegido).
- **Criterios:** ahorro real de tokens y contexto de sesión, ausencia de dependencias de código/scripts, decidido por el dueño del proyecto.
- **Consecuencias / impacto:** `new-use-case` pierde los pasos de arranque/cierre de tiempo; `progreso.md` y los docs dejan de referenciar `tiempos.md`; el ciclo de CU queda igual en lo funcional.
- **Estado:** Vigente.

## D-029 — Eliminación de `prompts_log.md`

- **Fecha:** 2026-10-13.
- **Decisión:** eliminar `prompts_log.md` y dejar de registrar el historial de prompts por CU, por decisión del usuario al optimizar el uso de tokens. El archivo era solo un artefacto de auditoría humana: el desarrollo no lo lee (el estado vive en `progreso.md` y en memoria/engram), así que mantenerlo costaba tokens de escritura sin aportar al flujo.
- **Contexto / problema:** se buscaba reducir el gasto de tokens del ciclo por CU; `prompts_log.md` era la única referencia pendiente tras D-028.
- **Alternativas consideradas:** (a) conservarlo con entradas mínimas (descartado: el usuario lo declara opcional y prefiere no mantenerlo); (b) eliminar el archivo y sus referencias activas (elegido).
- **Criterios:** ahorro real de tokens, cero dependencias de código/scripts (verificado por búsqueda en el repo).
- **Consecuencias / impacto:** se limpian las referencias en `AGENTS.md`, `README.md` y `new-use-case`; las entradas históricas de archived openspec/reviews que mencionaban `prompts_log.md` no se reescriben; el archivo sigue recuperable desde git.
- **Estado:** Vigente.

## D-030 — Alcance acordado de CU-07 (entrega de tareas)

- **Fecha:** 2026-10-13.
- **Decisión (acordada con el usuario; a formalizar en el design de CU-07):**
  1. **Naturaleza de la entrega:** solo texto y links (sin archivos adjuntos) por ahora; el modelo debe quedar preparado para admitir adjuntos en el futuro.
  2. **Cardinalidad:** una entrega por par (tarea, estudiante) con unique constraint; se modifica (A1) o elimina (A2) dentro del plazo.
  3. **Semántica de plazo:** la tarea se considera disponible con `active` y `due_date` no vencida, comparando en UTC normalizado; la entrega solo se permite antes de la fecha límite. Resuelve la limitación de tz de SQLite diferida desde CU-06.
  4. **Endpoints:** anidados y Estudiante-only: listar las tareas del curso con la entrega propia y `POST/PUT/DELETE /api/courses/<id>/tasks/<task_id>/submission`; listar entregas de otros queda para CU-08 (corrección).
- **Contexto / problema:** decisiones de diseño pedidas por el usuario antes de arrancar el ciclo `new-use-case` de CU-07.
- **Criterios:** fidelidad a `casos_de_uso.md` CU-07, simplicidad de alcance (sin infra de archivos), reutilización del modelo `Task` y de `get_manageable_course`.
- **Consecuencias / impacto:** CU-08 consumirá `Submission` para corregir y aplicará la regla "no corregida" de A1; CU-09 usará la entrega/no-entrega para el promedio.
- **Estado:** Acordada (pendiente de implementación en CU-07).

## D-031 — Endpoints de entrega y listado role-aware de tareas (CU-07)

- **Fecha:** 2026-10-13.
- **Decisión:** las entregas se exponen como subrecurso de la tarea en un blueprint nuevo `blueprints/submissions.py` con `url_prefix="/api/courses"` e `@login_required` + `@require_roles(UserRole.STUDENT)`: `POST/PUT/DELETE /api/courses/<id>/tasks/<task_id>/submission`. La entrega es única por par (tarea, estudiante) (`UniqueConstraint`), la eliminación es física, y la disponibilidad/plazo (`active` y `due_date` en UTC normalizado) se valida en `services/` con el orden D-I (401→403 rol→404 curso→403 sin inscripción activa→404 tarea→409 no disponible→400 datos→409 duplicado→404 entrega en PUT/DELETE). Se centralizan los helpers de plazo en `task_service` (`now_utc`, `as_utc`, `is_task_available`, `ensure_task_available`, `get_task_or_404`) y se hace role-aware el listado `GET /api/courses/<id>/tasks` (Profesor: todas; Estudiante: disponibles + entrega propia), con la forma de respuesta del Profesor sin cambios. Se extiende `GET /api/courses/mine` y `course_service.list_courses_for_user` al Estudiante (cursos con inscripción activa).
- **Contexto / problema:** CU-07 introduce al Estudiante como actor y necesita leer el estado de entrega junto con las tareas; había que decidir dónde vive la regla de plazo, cómo se autoriza al Estudiante y cómo se evita romper el contrato del Profesor.
- **Alternativas consideradas:** (a) endpoints de "mis entregas" desacoplados del curso — rechazado por perder el contexto del curso y duplicar autorización; (b) exponer el plazo de forma parcial en el listado del Profesor — rechazado por simplicidad y por mantener intacto su contrato; (c) subrecurso de tarea + listado role-aware (elegido), reutilizando `get_task_or_404` y los helpers de `task_service`.
- **Criterios:** fidelidad a `casos_de_uso.md` CU-07 (disponibilidad y plazo), reutilización del patrón de subrecurso de CU-05/CU-06, mínimo impacto en el contrato existente y concentración de la semántica de plazo en `services/`.
- **Consecuencias / impacto:** CU-08 consumirá `Submission` (corrección) y aplicará la regla "no corregida todavía" del paso A1.4; CU-09 usará la entrega/no-entrega para el promedio; el frontend del Estudiante usa `GET /api/courses/mine` para el selector de curso y el listado role-aware para el estado de entrega.
- **Estado:** Vigente.

## D-032 — Alcance acordado de CU-08 (corrección de tareas)

- **Fecha:** 2026-10-14.
- **Decisión (acordada con el usuario; formalizada en el design de CU-08):**
  1. **Aprobado/desaprobado derivado:** el estado se calcula de la calificación (aprobado con `grade >= 6`, desaprobado con `1 <= grade <= 5`) y **no se persiste**; se expone como `approved` calculado en el serializador.
  2. **Contenido de la corrección:** calificación entera (1..10) obligatoria y retroalimentación de texto opcional (máximo 5000 caracteres); sin estados intermedios.
  3. **Archivo corregido diferido:** el paso 10 de `casos_de_uso.md` CU-08 ("adjuntar un archivo corregido") queda fuera de alcance; el modelo no incorpora infraestructura de archivos.
  4. **Visibilidad del Estudiante diferida a CU-09:** `grade`/`feedback`/`graded_at` no se exponen al Estudiante en CU-08 (los serializadores del Estudiante enumeran campos explícitos); la consulta de calificaciones es el CU-09.
  5. **Sin requisito de inscripción activa:** la precondición es que exista la entrega; se puede corregir aunque la inscripción se haya desactivado después de entregar (D-030 punto 3).
  6. **Entrega corregida inmutable para el Estudiante:** tras la corrección, `PUT`/`DELETE` de la entrega propia responden 409 (regla "no corregida todavía" de A1.4).
- **Contexto / problema:** decisiones de diseño pedidas por el usuario antes de arrancar el ciclo `new-use-case` de CU-08; el CU-07 había diferido a CU-08 la regla "no corregida todavía" y a CU-09 la visibilidad de la nota.
- **Criterios:** fidelidad a `casos_de_uso.md` CU-08 (flujo principal + A1), simplicidad de alcance (sin infra de archivos ni notificaciones), reutilización de `get_manageable_course`/`get_task_or_404` y respeto de la frontera con CU-09.
- **Consecuencias / impacto:** el frontend del Profesor (pantalla `/grading`) consume los endpoints de corrección; CU-09 deberá decidir la forma en que el Estudiante ve su nota y retroalimentación; el promedio de CU-09 usa `grade` y la regla de no-entregadas fuera de plazo.
- **Estado:** Vigente.

## D-033 — Endpoints de corrección y derivación de la aprobación (CU-08)

- **Fecha:** 2026-10-14.
- **Decisión:** la corrección se expone en un blueprint nuevo `blueprints/grading.py` con `url_prefix="/api/courses"` e `@login_required` + `@require_roles(UserRole.TEACHER)`: `GET /api/courses/<id>/tasks/<task_id>/submissions` (listado con datos del estudiante y estado de corrección) y `PUT /api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade` (corregir o modificar). La lógica y las validaciones viven en `services/grading_service.py` (`list_submissions_for_task`, `grade_submission`, `_validate_grade`, `_is_approved`) con el orden curso asignado → tarea del curso → entrega existente → datos; `grade_submission` actualiza `grade`, `feedback` y `graded_at` (`datetime.now(UTC)`) tanto en el alta como en la modificación (A1). El estado aprobado/desaprobado se deriva en el serializador (`approved = grade is not None and grade >= 6`), sin columna propia ni migración de estado. La forma de la entrega del Estudiante no cambia: `_serialize_submission` en `blueprints/submissions.py` y `blueprints/tasks.py` enumeran campos explícitos y no incluyen los de corrección.
- **Contexto / problema:** CU-08 introduce la corrección sobre `Submission`; había que decidir dónde se valida la pertenencia de la tarea al curso, si la aprobación se persiste y cómo se evita filtrar la nota al Estudiante antes de CU-09.
- **Alternativas consideradas:** (a) persistir una columna `approved` — rechazado por redundante y propenso a desincronización respecto de `grade`; (b) reutilizar `blueprints/submissions.py` para el listado del Profesor — rechazado por mezclar dos actores y dos formas de respuesta en un blueprint Estudiante-only; (c) blueprint y servicio propios con derivación en el serializador (elegido), reutilizando `get_manageable_course` y `get_task_or_404`.
- **Criterios:** fidelidad a `casos_de_uso.md` CU-08 (flujo principal y A1) y a las reglas de negocio (calificación 1..10, promedio simple, sin correo), reutilización del patrón de subrecurso y de la autorización por rol (D-011/D-021), y mínimo impacto en el contrato del Estudiante.
- **Consecuencias / impacto:** el esquema cambia con la migración `0007_add_grading` (tres columnas nullable: `grade`, `feedback`, `graded_at`); el guard 409 en `submission_service.update_submission`/`delete_submission` (`submission.grade is not None`) cierra la regla A1.4 diferida desde CU-07; CU-09 reutilizará `grade`/`graded_at` para la consulta de calificaciones y el promedio.
- **Estado:** Vigente.

## D-034 — Alcance acordado de CU-09 (consulta de calificaciones)

- **Fecha:** 2026-10-14.
- **Decisión (acordada con el usuario; formalizada en el design de CU-09):**
  1. **Una consulta, dos vistas por rol:** el Estudiante ve el detalle por tarea (nota, retroalimentación y aprobado/desaprobado) más su promedio del curso; el Profesor ve la matriz estudiante × tarea con el promedio por estudiante y el promedio del curso. El Administrador no tiene acceso (403).
  2. **Promedio simple sobre tareas activas:** cada tarea activa aporta su nota si la entrega está corregida, aporta `1` si venció y no hay entrega, y no aporta nada si no está corregida o si el plazo no venció. El promedio es `null` si no hay ningún valor contribuyente.
  3. **Visibilidad del Estudiante habilitada:** CU-09 expone `grade`/`feedback`/`graded_at` y el estado derivado al Estudiante, cerrando la visibilidad que D-032.4 había diferido desde CU-08.
  4. **Sin cambios de esquema:** el CU se resuelve con consultas de solo lectura sobre `Task`, `Submission`, `Enrollment` y `User`; no hay migración.
  5. **Una sola unidad de entrega con `size:exception`:** el pronóstico de `tasks.md` (~1.100-1.400 líneas) supera el umbral de revisión de 400 líneas; el usuario aceptó una única unidad con excepción de tamaño en lugar de PRs encadenados (estrategia de entrega `exception-ok`).
- **Contexto / problema:** CU-09 es el CU que consumía lo que CU-08 había diferido (visibilidad de la corrección para el Estudiante) y el primero que agrega datos (promedios) en lugar de sólo exponerlos; había que fijar la regla exacta del promedio y quién ve qué.
- **Criterios:** fidelidad a `casos_de_uso.md` CU-09 (promedio simple; las no corregidas no entran; las no entregadas fuera de plazo cuentan como 1), exclusividad de roles (D-010), regla de negocio "los inactivos no se tratan como activos" y reutilización de la autorización por rol y de alcance ya existente.
- **Consecuencias / impacto:** el Estudiante accede por primera vez a sus notas; la lógica del promedio queda en `services/` (nunca en el cliente); el promedio del curso del Profesor se define como la media de los promedios por estudiante con al menos un valor (ver D-035).
- **Estado:** Vigente.

## D-035 — Endpoint de consulta, formas de respuesta por rol y agregación del promedio (CU-09)

- **Fecha:** 2026-10-14.
- **Decisión:** la consulta se expone en un blueprint nuevo `blueprints/grades.py` con `url_prefix="/api/courses"` e `@login_required` + `@require_roles(UserRole.TEACHER, UserRole.STUDENT)`: `GET /api/courses/<id>/grades`, que mapea `NotFoundError` → 404 y `ForbiddenError` → 403. La lógica vive en `services/grade_service.py` (`get_course_grades`, `_student_view`, `_teacher_view`, `_counted_value`, `_average`, `_active_tasks`, `_require_active_enrollment`) con el orden D-G: 401 en el guard → 403 por rol → 404 curso (`get_course_or_404`) → 403 de alcance (`get_manageable_course` para el Profesor; inscripción activa para el Estudiante). Formas de respuesta: Estudiante `{course, average, tasks:[{task_id, title, due_date, active, submitted, grade, feedback, graded_at, approved, counted, effective_value}]}` y Profesor `{course, tasks:[…], students:[{student, grades:{<task_id>: value|null}, average, approved}], course_average}`. El promedio del curso es la media simple de los promedios por estudiante que tienen al menos un valor; el promedio se devuelve **crudo** (sin redondear) y el redondeo es sólo de presentación en el cliente. `approved` se deriva de `APPROVAL_THRESHOLD` (reutilizado de `grading_service`), sin persistirlo: en la fila del Profesor es el estado de aprobación **del curso** del estudiante, con la regla `average >= 6` (falso cuando el promedio es nulo), ratificada por el usuario el 2026-10-16 y expuesta en la columna "Estado" de la vista del Profesor. El Estudiante usa un serializador propio y no reutiliza el de entregas. La regla "vencida" vive en el servidor con `now_utc()`/`as_utc()` (reutilizadas de `task_service`), y el cliente **deriva el estado de los flags del servidor** (`submitted`, `counted`, `effective_value`) sin recalcular el vencimiento — corrección del hallazgo M-01 de `reviews/cu-09.md`.
- **Contexto / problema:** había que decidir si el CU usaba uno o dos endpoints, de dónde salía el promedio del curso cuando hay estudiantes sin notas, y cómo evitar que el cliente duplicara la regla de vencimiento que ya estaba resuelta en el servidor desde CU-07.
- **Alternativas consideradas:** (a) un endpoint por rol — rechazado por duplicar autorización y selector de curso; (b) reutilizar el serializador de entregas del Estudiante — rechazado porque enumera campos y excluye la corrección, justamente lo que CU-09 debe exponer; (c) calcular el promedio del curso como media simple de **todas** las notas de la matriz — rechazado porque diluye el promedio con estudiantes sin ningún valor contribuyente; (d) recalcular el vencimiento en el cliente — descartado durante la revisión (M-01) por duplicar una regla de negocio y discrepar por zona horaria.
- **Criterios:** propagación de capas `routes → services → models`, regla del servidor como fuente de verdad, reutilización de helpers ya validados (`get_course_or_404`, `get_manageable_course`, `now_utc`, `as_utc`, `APPROVAL_THRESHOLD`) y mínimo impacto en los contratos de CU-06/07/08.
- **Consecuencias / impacto:** la matriz del Profesor resuelve todas las entregas del curso en una sola consulta (sin N+1); el Estudiante accede a `grade`/`feedback`/`graded_at`; queda registrada como deuda técnica (B-01 de `reviews/cu-09.md`) la convención preexistente de mostrar fechas naive-UTC como locales, que afecta a `tasks`, `submissions` y `grades`.
- **Estado:** Vigente.

## D-036 — Modo `--serve` desligado en `scripts/verify.py` para evidencia con servicios vivos

- **Fecha:** 2026-10-14.
- **Decisión:** `scripts/verify.py` incorpora el modo `--serve` (con `--db`, `--seed-demo`, `--seed-admin`), que levanta backend y Vite **desligados** del proceso del agente y retorna en segundos: en Windows usa `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB` con fallback a `DETACHED_PROCESS`, y en POSIX `start_new_session=True`. Registra los pids en `scripts/.verify-pids`, y `--cleanup` los detiene matando el árbol de procesos. El smoke (`--cu CU-0X`) mantiene su comportamiento previo de arrancar, validar y limpiar en una sola corrida.
- **Contexto / problema:** la evidencia UI de CU-09 (Playwright) necesita backend y Vite vivos **entre** tool calls; lanzarlos en primer plano desde el shell del agente mantiene abierto el árbol de procesos/stdio del llamador, y el tool call no retorna hasta que los servicios mueren (ver `errores.md`, 2026-10-14).
- **Alternativas consideradas:** (a) dejar los servicios en primer plano — descartado: el tool call no retorna y la interrupción los mata; (b) reutilizar `--keep` del smoke — insuficiente: encadena arranque, smoke y espera dentro de la misma corrida; (c) capturar la evidencia con servicios efímeros por captura — descartado por lento y frágil; (d) modo `--serve` desligado (elegido).
- **Criterios:** portabilidad (mismos pasos documentados para Windows/Linux/macOS), ausencia de procesos residuales (cleanup por árbol) y reutilización del harness existente en lugar de agregar dependencias.
- **Consecuencias / impacto:** `AGENTS.md` y `README.md` documentan `--serve`/`--cleanup` como el modo para evidencia UI; las 10 capturas de `evidencias/cu-09/` se produjeron con este modo; `taskkill /F /T` mata el árbol aunque los pid que escuchan sean hijos de los pid registrados.
- **Estado:** Vigente.
