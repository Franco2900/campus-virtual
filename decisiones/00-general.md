# Decisiones generales (transversales)

Decisiones que no pertenecen a un caso de uso puntual: stack, arquitectura, MCP, tooling, CI, proceso y evolución de infraestructura.

> El índice completo vive en [`README.md`](./README.md).

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
- **Actualización (2026-10-24):** el conjunto vigente es mayor al original. Se suman `playwright` (MCP local de UI e2e, D-012) y `github` (`github-mcp-server` en modo solo lectura, toolsets `repos,issues,pull_requests,actions`, declarado en la config global, token por `GITHUB_MCP_TOKEN`). El MCP `github` es apoyo para inspeccionar repositorio, issues, PRs y runs de Actions desde el agente; no interviene en el flujo de entrega por CU (commits y push con `git`, CI también consultable con `gh`). Ninguno de los dos es requisito para que la aplicación funcione.
- **Estado:** Vigente.

## D-004 — Medición de tiempos

- **Fecha:** 2026-10-09.
- **Decisión:** registrar los tiempos en `tiempos.md` por unidad de trabajo (wall-clock), con categorías (decisión, diseño, implementación, test, documentación, configuración, revisión) y totales acumulados.
- **Contexto / problema:** se requiere medir el tiempo total de desarrollo y desglosarlo (código, decisiones, etc.).
- **Alternativas consideradas:** (a) plugin de opencode para medir por tool-call (instrumentación automática, más precisa pero más trabajo); (b) medición manual por límites de unidad.
- **Criterios:** simplicidad, verificabilidad, disponibilidad inmediata.
- **Consecuencias / impacto:** la medición no separa con precisión "pensar" de "escribir"; queda registrado como mejora futura un plugin de instrumentación.
- **Estado:** Superada por D-028.

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

## D-023 — Migraciones de esquema con Flask-Migrate (Alembic)

- **Fecha:** 2026-10-11.
- **Decisión:** adoptar **Flask-Migrate** (`4.1.0`) con **Alembic** (`1.20.0`) integrado al factory (`Migrate(app, db)`) para evolucionar el esquema con migraciones versionadas en `backend/migrations/`. `db.create_all()` queda limitado a `app.config["TESTING"]`. La base existente se llevó al esquema pre-CU-04 con un **baseline** (`0001_baseline_pre_cu_04`) + `flask db stamp`; los cambios de CU-04 se aplican con migraciones incrementales (`0002` agrega `user.active` con `server_default` para el backfill de filas existentes; `0003` crea `course_teacher`). `scripts/verify.py` y `scripts/seed_admin.py` corren `flask db upgrade` sobre la base (temporal o real) antes de usarla. El código generado de `backend/migrations/` queda **excluido de ruff** (`extend-exclude` en `backend/pyproject.toml`).
- **Contexto / problema:** D-010 y AGENTS dejaban las migraciones para el primer CU que cambiara el esquema con datos; CU-04 agrega `user.active` (NOT NULL) sobre una tabla con filas y una tabla nueva —el primer cambio de esquema con datos—.
- **Alternativas consideradas:** (a) seguir con `db.create_all()` (no agrega columnas nuevas ni hace backfill); (b) SQL manual (no portable ni versionado); (c) Flask-Migrate/Alembic (elegida).
- **Criterios:** versionado del esquema, portabilidad Windows/Linux/macOS, backfill reproducible, tooling estándar de Flask.
- **Consecuencias / impacto:** todo CU que cambie el esquema debe generar una migración (skill `create-migration`); `migrations/` se versiona en git (no se ignora); `db.create_all()` queda sólo para tests; el baseline pre-CU-04 documenta el punto de arranque.
- **Estado:** Vigente.

## D-028 — Eliminación de la medición de tiempos y la skill `track-time`

- **Fecha:** 2026-10-13.
- **Decisión:** eliminar `tiempos.md` y la skill `track-time` (`.opencode/skills/track-time/`) y dejar de registrar tiempos por unidad de trabajo, por decisión del usuario al optimizar el uso de tokens: calcular el tiempo no es necesario para el proyecto. **Supersede a D-004.** Se limpian todas las referencias activas (tabla de skills en `AGENTS.md`, mapa de archivos en `AGENTS.md`/`README.md`, protocolo de "Fases y sesiones", pasos de `new-use-case` y `.atl/skill-registry.md`); los archivos eliminados siguen recuperables desde git; las entradas históricas (archived openspec, `reviews/`, `errores/`, `prompts_log.md`) no se reescriben.
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

## D-036 — Modo `--serve` desligado en `scripts/verify.py` para evidencia con servicios vivos

- **Fecha:** 2026-10-14.
- **Decisión:** `scripts/verify.py` incorpora el modo `--serve` (con `--db`, `--seed-demo`, `--seed-admin`), que levanta backend y Vite **desligados** del proceso del agente y retorna en segundos: en Windows usa `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB` con fallback a `DETACHED_PROCESS`, y en POSIX `start_new_session=True`. Registra los pids en `scripts/.verify-pids`, y `--cleanup` los detiene matando el árbol de procesos. El smoke (`--cu CU-0X`) mantiene su comportamiento previo de arrancar, validar y limpiar en una sola corrida.
- **Contexto / problema:** la evidencia UI de CU-09 (Playwright) necesita backend y Vite vivos **entre** tool calls; lanzarlos en primer plano desde el shell del agente mantiene abierto el árbol de procesos/stdio del llamador, y el tool call no retorna hasta que los servicios mueren (ver `errores/00-general.md`, 2026-10-14).
- **Alternativas consideradas:** (a) dejar los servicios en primer plano — descartado: el tool call no retorna y la interrupción los mata; (b) reutilizar `--keep` del smoke — insuficiente: encadena arranque, smoke y espera dentro de la misma corrida; (c) capturar la evidencia con servicios efímeros por captura — descartado por lento y frágil; (d) modo `--serve` desligado (elegido).
- **Criterios:** portabilidad (mismos pasos documentados para Windows/Linux/macOS), ausencia de procesos residuales (cleanup por árbol) y reutilización del harness existente en lugar de agregar dependencias.
- **Consecuencias / impacto:** `AGENTS.md` y `README.md` documentan `--serve`/`--cleanup` como el modo para evidencia UI; las 10 capturas de `evidencias/cu-09/` se produjeron con este modo; `taskkill /F /T` mata el árbol aunque los pid que escuchan sean hijos de los pid registrados.
- **Estado:** Vigente.

## D-042 — Subagentes del proyecto denegados por la allowlist del orquestador

- **Fecha:** 2026-10-19.
- **Decisión:** agregar los agentes del proyecto (`backend`, `frontend`, `database`, `tester`, `reviewer`) a la allowlist `permission.task` del agente primario `gentle-orchestrator` en la configuración global de OpenCode.
- **Contexto / problema:** las revisiones de CU-08 a CU-11 se hicieron con un worker general + skill `review-use-case` inline porque el subagente `reviewer` «no estaba disponible como tipo de agente». Causa raíz encontrada: la allowlist del orquestador usa `"*": "deny"` y solo habilita agentes gentle-ai, de modo que **ningún** agente definido en `.opencode/agents/` del proyecto era invocable (no era un problema del `reviewer` ni del proveedor: el error de tier documentado en `errores/00-general.md` fue un síntoma anterior y transitorio).
- **Alternativas consideradas:** registrar los agentes en `opencode.json` del proyecto (la restricción vive en el agente primario de la config global; registrar en el proyecto no la relaja — descartada); seguir con la skill inline (workaround permanente, descartada).
- **Criterios:** cambio mínimo y reversible en la config del orquestador; sin tocar los `.md` de los agentes (su frontmatter era correcto).
- **Consecuencias / impacto:** la config global está marcada `__managed_by: gentle-ai/sdd`; un sync de gentle-ai puede sobrescribir la allowlist y reintroducir la denegación. Requiere reiniciar OpenCode para tomar efecto. Si se pierde, repetir este cambio.
- **Estado:** Vigente.
