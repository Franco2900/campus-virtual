# AGENTS.md

Instrucciones persistentes para agentes de IA (opencode) que trabajan en este proyecto.
Este archivo es la fuente de verdad operativa. El README es para humanos.

## Proyecto

- **Nombre:** Campus Virtual.
- **Propósito:** sistema web completo (backend + frontend) que gestiona cursos, usuarios, inscripciones, tareas y calificaciones con tres roles (Estudiante, Profesor, Administrador) y un chatbot integrado.
- **Contexto:** Trabajo Práctico Integrador (UNLa), Grupo 12. El foco de evaluación es la orquestación de AI Engineering y la funcionalidad, no la estética.
- **Componentes:** backend Flask (API REST), frontend React + Vite, base SQLite vía SQLAlchemy, chatbot LangChain + Ollama local.

## Cómo ejecutar

Comandos reales (verificados al implementar CU-01). En Windows, `npm` y `openspec` deben invocarse con el prefijo `cmd /c` por la execution policy de PowerShell (ver D-006); en Linux/macOS se omiten el prefijo `cmd /c` y los sufijos `.exe`.

- **Backend — instalación (una vez, desde la raíz del proyecto):**
  - `python -m venv .venv`
  - Windows: `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt`
  - Linux/macOS: `.venv/bin/python -m pip install -r backend/requirements.txt`
- **Backend (dev):** `.\.venv\Scripts\python.exe backend\app.py` (Windows) / `.venv/bin/python backend/app.py` (Linux/macOS) → `http://127.0.0.1:5000`. Base SQLite en `backend/instance/campus.db` (override con `CAMPUS_DB_PATH`; `SECRET_KEY` por entorno).
- **Backend — migraciones:** desde `backend/`, Windows `..\.venv\Scripts\python.exe -m flask --app app db upgrade`; Linux/macOS `../.venv/bin/python -m flask --app app db upgrade`. Aplica las migraciones pendientes (`scripts/seed_admin.py`, `scripts/seed_demo.py` y `scripts/verify.py` también las aplican). Esquema versionado con Flask-Migrate/Alembic (D-023).
- **Frontend (dev):** dentro de `frontend/`, `npm install` y `npm run dev` (Windows: `cmd /c npm install`, `cmd /c npm run dev`) → `http://localhost:5173`, con proxy de desarrollo `/api` → `http://localhost:5000`. Build: `npm run build`.
- **Tests (backend):** dentro de `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest`; Linux/macOS `../.venv/bin/python -m pytest`.
- **Lint / formato (backend):** desde la raíz, Windows `.\.venv\Scripts\python.exe -m ruff check backend` y `.\.venv\Scripts\python.exe -m ruff format --check backend`; Linux/macOS `.venv/bin/python -m ruff ...`. Aplicar: `-m ruff check backend --fix` y `-m ruff format backend`.
- **Lint / formato (frontend):** dentro de `frontend/`, Windows `cmd /c npm run lint:format` (check) / `cmd /c npm run lint:format:fix` (aplica); Linux/macOS `npm run ...`.

## Arquitectura

- **Patrón:** capas + Blueprints por dominio (Flask).
- **Regla de dependencias:** `routes → services → models`. La lógica de negocio vive en `services/`, nunca en `routes/` ni en los modelos.
- **Estructura backend:**

```
backend/
├── app.py            # factory: crea la app, registra blueprints, inicializa DB
├── blueprints/       # una por dominio: auth, courses, users, tasks, enrollments, grades
├── services/         # lógica de negocio y validaciones
├── models/           # entidades SQLAlchemy
├── config/           # configuración (DB path, secretos por env)
└── migrations/       # migraciones Alembic (Flask-Migrate)
```

- **Persistencia:** toda consulta a la base se hace desde `services/` a través de los modelos SQLAlchemy. No hay SQL crudo en `routes/`.
- **Validaciones:** en la capa `services/`.
- **Esquema:** SQLite versionado con migraciones (Flask-Migrate/Alembic, `backend/migrations/`, D-023); `flask db upgrade` aplica lo pendiente, y `db.create_all()` queda sólo para tests (`app.config["TESTING"]`). Un CU que cambie el esquema con datos genera una migración (skill `create-migration`); `migrations/` se versiona y queda excluido de ruff.
- **Frontend:** organización por feature (`src/features/<feature>/`), con `src/api/client.js` como cliente HTTP base; componentes en `PascalCase`. Las validaciones de servidor son la fuente de verdad: el cliente solo envía y muestra los errores devueltos por el backend.
- **Frontend — design system:** UI construida sobre un design system propio sobre Bootstrap (D-019): tokens en `src/theme/tokens.css` (color por rol, semánticos, neutros; claro/oscuro), tema con `src/theme/ThemeProvider.jsx` (`data-bs-theme` + `localStorage` `campus-theme`), componentes reutilizables en `src/ui/` (`Button`, `Card`, `Badge`, `RoleBadge`, `PageHeader`, `Spinner`, `EmptyState`, `DataTable`, `FormField`, `Modal`, `ConfirmDialog`, `Toast`) y shell de app en `src/app/` (`AppLayout`, `Navbar`, `Sidebar`, `ProtectedRoute`, `HomePage`). Animaciones con `motion` (D-020). Regla: reutilizar tokens y componentes, sin colores hardcodeados ni CDN; usar `data-testid` en los elementos que la evidencia necesita. Contrato detallado en la skill `design-system`.
- **Chatbot:** implementado (CU-11, D-039/D-040): agente LangChain + Ollama local (`qwen3:4b`, configurable por env) en `backend/services/chat_service.py`, blueprint `backend/blueprints/chat.py` (`POST/GET /api/chat/messages`), persistencia de historial en `conversation`/`message` (migración `0008`) y pantalla `/chat` en `frontend/src/features/chatbot/`. Herramientas de solo lectura (`build_tools`) scopeadas por la sesión del usuario (identidad y permisos SIEMPRE desde Flask, nunca del modelo); el agente no muta datos ni califica. Historial: ventana de 10 mensajes por turno; fallo de Ollama → 502 con mensaje amable y el turno **no** se persiste.

## Casos de uso

Resumen (detalle completo en `casos_de_uso.md`):

| ID | Nombre | Actor |
|----|--------|-------|
| CU-01 | Registrarse | Usuario no registrado |
| CU-02 | Autenticarse | Usuario |
| CU-03 | Gestionar cursos | Administrador |
| CU-04 | Gestionar usuarios | Administrador |
| CU-05 | Gestionar inscripciones | Administrador / Profesor |
| CU-06 | Gestionar tareas | Profesor |
| CU-07 | Entregar tarea | Estudiante |
| CU-08 | Corregir tarea | Profesor |
| CU-09 | Consultar calificaciones | Profesor / Estudiante |
| CU-10 | Filtrar usuarios | Administrador |
| CU-11 | Utilizar chatbot de asistencia | Usuario autenticado |

### Reglas de negocio clave

- Cada usuario tiene **exactamente un rol** (mutuamente excluyentes). Los nuevos son Estudiante; Profesor lo asigna un Administrador.
- El correo electrónico es identificador único de la cuenta.
- Cursos y tareas pueden estar activos o inactivos; los inactivos no se tratan como activos.
- Calificaciones entre 1 y 10. Promedio simple. Tareas no corregidas no entran al promedio; tareas no entregadas fuera de plazo cuentan como 1.
- Un Profesor solo opera sobre los cursos en los que trabaja.
- Inscripciones, modificaciones de tareas y correcciones **no** generan notificaciones por correo.

## Mapa de archivos

```
/
├── AGENTS.md            # este archivo (instrucciones para agentes)
├── README.md            # documentación para humanos
├── opencode.json        # configuración de proyecto (MCP, permisos)
├── casos_de_uso.md      # especificación de los 10 CU
├── decisiones.md        # registro de decisiones técnicas/arquitectónicas
├── errores.md           # bitácora de errores
├── progreso.md          # control de progreso
├── evidencias/          # screenshots de verificación por CU (evidencia visual)
├── reviews/             # artefactos de revisión por CU (hallazgos, veredicto, mapa de evidencia)
├── docs/                # documentación de soporte (docs/er-diagrama.md: diagrama entidad-relación)
├── scripts/             # utilidades portables: verify.py, seed_admin.py, seed_demo.py, smoke_cu0X.py
├── backend/             # API Flask (app.py, config/, models/, services/, blueprints/, migrations/, tests/)
├── frontend/            # SPA React + Vite (src/api/, src/features/, src/theme/, src/ui/, src/app/)
├── openspec/            # specs spec-driven (openspec): fuente de verdad de specs
├── .atl/
│   └── skill-registry.md  # índice de skills (generado)
└── .opencode/
    ├── agents/          # subagentes: backend, frontend, database, tester, reviewer
    ├── commands/        # comandos /opsx-* del CLI openspec (generados)
    └── skills/          # skills: new-use-case, create-crud, create-migration, run-verification, design-system, openspec-*
```

> No documentar ni referenciar archivos que no existan todavía.

## API

| Método | Ruta | CU | Propósito | Auth |
|--------|------|----|-----------|------|
| POST | `/api/auth/register` | CU-01 | Registrar una cuenta (rol Estudiante) | Público |
| POST | `/api/auth/login` | CU-02 | Iniciar sesión (emite cookie de sesión) | Público |
| GET | `/api/auth/me` | CU-02 | Obtener el usuario autenticado | Sesión |
| POST | `/api/auth/logout` | CU-02 | Cerrar sesión (idempotente; sin sesión responde 200) | Sesión |
| GET | `/api/courses` | CU-03 | Listar cursos (incluye inactivos) | Sesión + Administrador |
| POST | `/api/courses` | CU-03 | Crear un curso (201/400/409) | Sesión + Administrador |
| GET | `/api/courses/<id>` | CU-03 | Obtener un curso (200/404) | Sesión + Administrador |
| PUT | `/api/courses/<id>` | CU-03 | Editar un curso (200/400/404/409) | Sesión + Administrador |
| PATCH | `/api/courses/<id>` | CU-03 | Activar/desactivar un curso — body `{"active": <bool>}` (200/400/404) | Sesión + Administrador |
| GET | `/api/users` | CU-04/CU-10 | Listar usuarios (incluye inactivos); filtros opcionales `q` (texto libre), `role` y `active` (`true`/`false`), combinados con AND (400 con criterio inválido) | Sesión + Administrador |
| GET | `/api/users/<id>` | CU-04 | Obtener un usuario (200/404) | Sesión + Administrador |
| PUT | `/api/users/<id>` | CU-04 | Editar datos y rol (200/400/404/409) | Sesión + Administrador |
| PATCH | `/api/users/<id>` | CU-04 | Activar/desactivar — body `{"active": <bool>}` (200/400/404) | Sesión + Administrador |
| POST | `/api/users/<id>/password` | CU-04 | Resetear contraseña — body `{"password": "..."}` (200/400/404) | Sesión + Administrador |
| GET | `/api/courses/<id>/teachers` | CU-04 | Listar profesores del curso (200/404) | Sesión + Administrador |
| POST | `/api/courses/<id>/teachers` | CU-04 | Asignar profesor — body `{"teacher_id": <id>}` (201/400/404/409) | Sesión + Administrador |
| DELETE | `/api/courses/<id>/teachers/<teacher_id>` | CU-04 | Quitar profesor del curso (200/404) | Sesión + Administrador |
| GET | `/api/courses/mine` | CU-05 | Listar los cursos del usuario (Profesor: asignados; Estudiante: inscritos; Admin: todos) | Sesión + Administrador/Profesor/Estudiante |
| GET | `/api/courses/<id>/students` | CU-05 | Listar estudiantes activos con su inscripción (200/403/404) | Sesión + Administrador/Profesor |
| POST | `/api/courses/<id>/students` | CU-05 | Inscribir estudiante — body `{"student_id": <id>}` (201/400/403/404/409) | Sesión + Administrador/Profesor |
| PATCH | `/api/courses/<id>/students/<student_id>` | CU-05 | Activar/desactivar inscripción — body `{"active": <bool>}` (200/400/403/404/409) | Sesión + Administrador/Profesor |
| DELETE | `/api/courses/<id>/students/<student_id>` | CU-05 | Eliminar inscripción (200/403/404) | Sesión + Administrador/Profesor |
| GET | `/api/courses/<id>/tasks` | CU-06/07 | Listar tareas del curso (Profesor: activas e inactivas; Estudiante: disponibles + entrega propia) (200/403/404) | Sesión + Profesor/Estudiante |
| POST | `/api/courses/<id>/tasks` | CU-06 | Crear una tarea (201/400/403/404/409) | Sesión + Profesor |
| GET | `/api/courses/<id>/tasks/<task_id>` | CU-06 | Obtener una tarea (200/403/404) | Sesión + Profesor |
| PUT | `/api/courses/<id>/tasks/<task_id>` | CU-06 | Editar una tarea, incl. fecha límite (200/400/403/404/409) | Sesión + Profesor |
| PATCH | `/api/courses/<id>/tasks/<task_id>` | CU-06 | Activar/desactivar tarea — body `{"active": <bool>}` (200/400/403/404) | Sesión + Profesor |
| POST | `/api/courses/<id>/tasks/<task_id>/submission` | CU-07 | Entregar una tarea — body `{"content", "links"}` (201/400/403/404/409) | Sesión + Estudiante |
| PUT | `/api/courses/<id>/tasks/<task_id>/submission` | CU-07 | Modificar la entrega propia (200/400/403/404/409) | Sesión + Estudiante |
| DELETE | `/api/courses/<id>/tasks/<task_id>/submission` | CU-07 | Eliminar la entrega propia (200/403/404/409) | Sesión + Estudiante |
| GET | `/api/courses/<id>/tasks/<task_id>/submissions` | CU-08 | Listar las entregas de la tarea con datos del estudiante y estado de corrección (200/403/404) | Sesión + Profesor |
| PUT | `/api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade` | CU-08 | Corregir o modificar una entrega — body `{"grade": 1..10, "feedback"?: str}` (200/400/403/404) | Sesión + Profesor |
| GET | `/api/courses/<id>/grades` | CU-09 | Consultar calificaciones del curso según el rol (Estudiante: sus notas, retroalimentación y promedio; Profesor: matriz estudiante × tarea y promedio del curso) (200/401/403/404) | Sesión + Profesor/Estudiante |
| POST | `/api/chat/messages` | CU-11 | Enviar una consulta al chatbot y obtener la respuesta del asistente — body `{"content": "..."}` (201/400/401/502) | Sesión + Estudiante/Profesor/Administrador |
| GET | `/api/chat/messages` | CU-11 | Obtener el historial de la conversación del usuario autenticado (200/401) | Sesión + Estudiante/Profesor/Administrador |

> Se completa a medida que se implementan los CU. No inventar endpoints.

## Convenciones

> PENDIENTE DE DEFINIR los detalles. Reglas mínimas ya fijadas:

- **Idioma del código e identificadores:** inglés.
- **Idioma de la documentación (README, AGENTS, docs):** español (neutral).
- **Idioma de la UI y mensajes al usuario:** español (neutral).
- **Backend:** `snake_case` para variables y funciones, `PascalCase` para clases, archivos en `snake_case`.
- **Frontend:** `camelCase` para variables y funciones, `PascalCase` para componentes y sus archivos, archivos de módulos en `camelCase` (p. ej. `client.js`).
- **Comentarios:** ninguno por defecto. Solo cuando expliquen una decisión, restricción o comportamiento no evidente.
- **Indentación / formato:** `ruff format` (Python) y `Prettier` (JS/JSX), configuración en `backend/pyproject.toml` y `frontend/.prettierrc` (ver "Cómo ejecutar").

## Verificación

Comandos reales (verificados en CU-01):

- **Backend:** dentro de `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest`; Linux/macOS `../.venv/bin/python -m pytest`.
- **Frontend:** dentro de `frontend/`, `npm run build` (Windows: `cmd /c npm run build`).
- **Smoke CU-01:** levantar backend y frontend y probar `POST /api/auth/register` (alta 201 + duplicado 409).
- **Smoke HTTP general:** `.\.venv\Scripts\python.exe scripts\verify.py [--cu CU-0X]` — arranca backend + Vite, readiness, corre el smoke del CU (`scripts/smoke_cu0X.py`, patrón `smoke_cu02.py`) contra el proxy y **cleanup garantizado** (detecta puertos ocupados y aborta sin duplicar servicios; mata el árbol de procesos). `--keep` deja los servicios vivos para el smoke UI con Playwright (pids en `scripts/.verify-pids`); `--cleanup` detiene los registrados; `--diagnose` muestra en solo lectura puertos ocupados y pids registrados.
- **Servicios vivos para evidencia UI:** `.\.venv\Scripts\python.exe scripts\verify.py --serve [--db backend\instance\campus.db] [--seed-demo]` — levanta backend + Vite **desligados** del proceso del agente (Windows: `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB` con fallback a `DETACHED_PROCESS`; POSIX: `start_new_session=True`), espera el readiness y **retorna en segundos** dejando los pids en `scripts/.verify-pids`; se cierra con `--cleanup`. Es el modo correcto para capturar screenshots con Playwright. **Gotcha:** lanzar los servicios en primer plano desde el shell del agente mantiene abierto el árbol de procesos/stdio del llamador y el tool call **no retorna nunca** (interrumpirlo mata el árbol); usar siempre `--serve` (ver `errores.md`).

- No declarar una tarea completada sin haber ejecutado su verificación.
- Conservar mensajes de error completos.
- Un CU se considera Completo solo cuando: funcionalidad implementada, código ejecutando, tests ejecutados, documentación y `progreso.md` actualizados (ver criterios en la plantilla).

## Evidencia y revisiones

- Screenshots por CU en `evidencias/cu-0X/` con nombres estandarizados `NN-accion.png` (full-page cuando aporte), cada uno ligado a un paso probado.
- Cada cierre de CU persiste `reviews/cu-0X.md`: hallazgos con `archivo:línea`, severidad (Bloqueante/Alta/Media/Baja), veredicto (APROBADO/RECHAZADO) y mapa de evidencia.
- Gate de evidencia: los screenshots deben mostrar el estado esperado (o salida real de smoke/tests si el CU no es visual) y la consola no debe tener errores inesperados.
- La revisión se ejecuta con el subagente `reviewer`; si no está disponible (error de tier del proveedor), con la skill `review-use-case` inline.

## Progreso visible (heartbeat)

- Reportar avance en cada turno de trabajo: qué se está haciendo, qué sigue, y estado de la todo list. No dejar pasajes largos sin salida al usuario.
- Antes de un tool call largo (tests, build, subagente): avisar qué se ejecuta y la duración estimada; si supera ~2-3 min sin salida, reportarlo explícitamente.
- Partir tareas grandes en pasos cortos y verificables, con su verificación (tests/build) en cada paso; mantener la todo list actualizada en tiempo real.
- Delegar en subagentes trabajo acotado y sin tramos silenciosos; si hay pasos largos, exigir reportes intermedios.
- Commitear por unidad de trabajo concluida para preservar avance y marcar hitos (skill `work-unit-commits`).

## Fases y sesiones

- Trabajar **un CU por fase** y, en lo posible, **una sesión por CU** (o por unidad de trabajo grande). Las sesiones largas sin corte degradan el contexto del agente.
- Señales para iniciar una sesión nueva:
  - El contexto del agente está muy cargado: respuestas degradadas, tool outputs truncados con frecuencia o aviso de "contexto extenso" en la sesión actual.
  - Se cierra un hito: un CU completo (después del archive y los commits) o una unidad de trabajo grande.
  - Antes de arrancar un CU nuevo (sprint de CU = sesión limpia).
- Protocolo de cierre de sesión:
  1. Commitear la unidad en curso (skill `work-unit-commits`).
  2. Pedir al agente que ejecute `mem_session_summary` con el estado completo.
  3. Cerrar y abrir una sesión nueva.
  4. Al retomar, el agente carga `mem_context`/`mem_search`, lee de `progreso.md` solo la sección del CU activo y continúa donde quedó (nunca asumir que el estado anterior sigue vivo; ver "Optimización de tokens").
- Gotcha operativo: "no ver avance en el terminal" NO significa cuelgue (ver `errores.md`); antes de asumir una traba, consultar `python scripts/verify.py --diagnose` y el estado del working tree.

## Optimización de tokens (convenciones)

- **Tests acotados en iteración:** durante la implementación correr solo los tests del dominio afectado (p. ej. `..\.venv\Scripts\python.exe -m pytest tests/test_tasks.py -q`); el suite completo (`-m pytest`) y el build/lint solo en el gate de cierre del CU.
- **Salida acotada:** pytest con `-q`; no imprimir salidas de éxito largas ni logs completos; si la salida es enorme, buscar con grep en el archivo capturado en vez de imprimirla entera.
- **Retomar sesión sin releer todo:** al retomar, cargar `mem_context`/`mem_search` y leer de `progreso.md` solo la sección del CU activo; no releer `AGENTS.md` a mano (el runtime ya lo inyecta).
- **Playwright quirúrgico:** si un paso de evidencia falla o se pierde, re-capturar solo las pantallas afectadas, no el flujo completo.
- **Delegar el "¿qué cambió?" al retomar:** si la comprensión del sprint anterior requiere leer 4+ archivos, delegar a un subagente el resumen del diff (~10 líneas) en vez de llenar el contexto del orquestador.

## Portabilidad

- **Objetivo:** el sistema (backend + frontend) debe correr en **Windows, Linux y macOS** con los pasos de "Cómo ejecutar".
- Rutas relativas al proyecto; sin rutas absolutas en el código de la app.
- Sin comandos, separadores ni rutas exclusivos de una plataforma en el código y scripts de la app.
- Documentar los requisitos específicos por SO cuando existan.
- La configuración local de herramientas (p. ej. `opencode.json`: ruta del MCP filesystem y forma del comando) es **tooling específico de la máquina**, no forma parte del sistema portable. No replicar patrones de esa config en el código de la app.

## Roadmap

- **Ahora:** Fase 6 en marcha — **CU-01 (Registrarse), CU-02 (Autenticarse), CU-03 (Gestionar cursos), CU-04 (Gestionar usuarios), CU-05 (Gestionar inscripciones), CU-06 (Gestionar tareas), CU-07 (Entregar tarea), CU-08 (Corregir tarea), CU-09 (Consultar calificaciones), CU-10 (Filtrar usuarios) y CU-11 (Utilizar chatbot de asistencia) implementadas, verificadas y cerradas**; **design system de frontend implementado y verificado** (cambio `add-frontend-design-system` archivado, D-019/D-020). CU-06 (cambio `add-task-management`): modelo `Task` + migración `0005`, endpoints anidados de tareas (Profesor-only), refactor de `get_manageable_course` a `course_service`, pantalla `/tasks`, **153 tests** backend, smoke HTTP 29/29, evidencia UI Playwright (claro/oscuro), revisión APROBADA (`reviews/cu-06.md`) y cambio archivado como `2026-10-13-add-task-management`. CU-07 (cambio `add-task-submission`): modelo `Submission` + migración `0006`, endpoints de entrega (Estudiante-only), listado de tareas role-aware y `/api/courses/mine` extendido al Estudiante, pantalla `/submissions`, **181 tests** backend, smoke HTTP 39/39, evidencia UI Playwright (claro/oscuro), revisión APROBADA (`reviews/cu-07.md`) y cambio archivado como `2026-10-13-add-task-submission`. CU-08 (cambio `add-task-grading`): `Submission` extendido con `grade`/`feedback`/`graded_at` + migración `0007`, endpoints de corrección (Profesor-only), guard 409 para entregas ya corregidas, aprobado/desaprobado derivado de la nota y pantalla `/grading`, **208 tests** backend, smoke HTTP 35/35, evidencia UI Playwright (claro/oscuro), revisión APROBADA (`reviews/cu-08.md`) y cambio archivado como `2026-10-14-add-task-grading`. CU-09 (cambio `add-grade-consultation`): `services/grade_service.py` + `blueprints/grades.py` (`GET /api/courses/<id>/grades`), dos vistas por rol (Estudiante: detalle + promedio; Profesor: matriz + promedio del curso), promedio sobre tareas activas (nota, `1` si venció sin entrega), visibilidad de la corrección habilitada al Estudiante (cierra D-032.4), sin migración, pantalla `/grades`, **221 tests** backend, smoke HTTP 35/35, evidencia UI Playwright (claro/oscuro), revisión APROBADA con 1 hallazgo Medio corregido (`reviews/cu-09.md`) y cambio archivado como `2026-10-14-add-grade-consultation`. CU-10 (cambio `add-user-filtering`): filtrado del listado de usuarios (`q`/`role`/`active` combinados con AND, escaping de comodines, validaciones 400), barra de filtros con debounce y estado vacío A1 diferenciado en `UsersPage`, smoke HTTP 22/22, **241 tests** backend, evidencia UI Playwright (9 screenshots claro/oscuro), revisión APROBADA (`reviews/cu-10.md`) y cambio archivado como `2026-10-16-add-user-filtering`. **CU-11 (cambio `add-chatbot-assistant`):** chatbot LangChain + Ollama local (`qwen3:4b`) con herramientas de solo lectura scopeadas por sesión, modelos `Conversation`/`Message` + migración `0008`, blueprint `chat.py` (`POST/GET /api/chat/messages`), pantalla `/chat`, **268 tests** backend, smoke HTTP 9/9, evidencia UI Playwright (claro/oscuro), revisión APROBADA (`reviews/cu-11.md`, 3 hallazgos Baja) y cambio archivado como `2026-10-17-add-chatbot-assistant`.
- **Activo:** pipeline spec-driven por CU vía `new-use-case` (propose → specs → design → tasks → apply → verify → archive) con revisión obligatoria antes de marcar Completo. Bootstrap del Administrador con `scripts/seed_admin.py` (`CAMPUS_ADMIN_EMAIL`/`CAMPUS_ADMIN_PASSWORD` obligatorias, D-017) y datos de prueba ampliados con `scripts/seed_demo.py` (idempotente; Profesores/Estudiantes/asignaciones/inscripciones); `scripts/verify.py --cu cu0X` corre contra una base temporal aislada sembrada y migrada, y `--serve` deja servicios desligados para la evidencia UI (D-036). Nota: el subagente `reviewer` no está disponible como tipo de agente en las sesiones de CU-08, CU-09, CU-10 y CU-11 (tampoco lo estuvo por tier del proveedor en CU-01 a CU-07, ver `errores.md`); se revisa inline con la skill `review-use-case`. Deuda técnica de `reviews/cu-09.md` (B-01: fechas naive-UTC mostradas como locales en `tasks`/`submissions`/`grades`) y B-04 (`GradingPage` listaba tareas inactivas) **resueltas** el 2026-10-19 con el helper `frontend/src/api/dates.js` (D-041).
- **Futuro:** sin ítems pendientes del alcance original (el chatbot, último ítem, está implementado).

## Límites

- No reemplazar tecnologías ni versiones del stack sin autorización.
- No introducir dependencias nuevas si ya existe una adecuada.
- No rediseñar la arquitectura existente por preferencia personal.
- No implementar funcionalidad fuera del alcance de los 10 CU.
- No tocar archivos marcados como generados (cuando existan).

## MCP y herramientas

- **engram** (memoria, local, config global): memoria persistente del proyecto. Usar para recordar decisiones y gotchas; no reemplaza a `decisiones.md`/`progreso.md`.
- **context7** (documentación, remoto/externo, config global): consultar docs actualizadas antes de escribir código de librerías (Flask, SQLAlchemy, React, Vite, LangChain). Evita APIs inventadas.
- **playwright** (UI e2e, local, `opencode.json`): navegar, completar formularios y capturar screenshots como evidencia de UI por CU (D-012). Requiere el browser instalado: `cmd /c npx -y @playwright/mcp@latest install-browser chrome-for-testing`.
- **Terminal:** herramienta nativa de opencode.
- **openspec CLI** (spec-driven): herramienta nativa del CLI; en Windows invocar siempre `cmd /c openspec ...` (mismo bloqueo de execution policy que `npx`, ver D-006). Los comandos `/opsx-*` omiten esa complejidad.
- Requisito de la consigna: mínimo 2 servidores MCP, al menos 1 externo (se cumple con engram + context7 + filesystem).

## Skills y subagentes

Skills del proyecto (`.opencode/skills/`, registradas en `.atl/skill-registry.md`):

| Skill | Cuándo |
|-------|--------|
| `new-use-case` | Ciclo completo de un CU (planificar e implementar) |
| `create-crud` | Abm/CRUD de una entidad (modelo + servicio + rutas + React) |
| `create-migration` | Cambios de esquema con migraciones |
| `run-verification` | Verificar tests/build antes de declarar algo terminado |
| `review-use-case` | Checklist de revisión de un CU (inline del subagente `reviewer`, con gate de evidencia) |
| `design-system` | Construir UI sobre `src/ui/` + tokens (`src/theme`) + shell (`src/app`) + `motion`; cómo agregar componentes, color por rol, temas claro/oscuro y evidencia |
| `openspec-*` (6) | Vía nativa del CLI openspec: propose, explore, update-change, apply-change, sync-specs, archive-change (comandos `/opsx-*`) |

Subagentes (`.opencode/agents/`): `backend`, `frontend`, `database`, `tester`, `reviewer` (read-only). Usarlos delegando trabajo específico; el `reviewer` es obligatorio antes de marcar un CU como Completo (si el subagente no está disponible por error de tier del proveedor, ejecutar la skill `review-use-case` inline).

Recomendar skills y subagentes nuevos cuando un patrón se repita o una tarea sea recurrente; no crear por cumplir inventario.

## Seguridad y gotchas

- **Nunca** escribir secretos, tokens ni credenciales en el código; usar variables de entorno.
- **Nunca** almacenar credenciales en archivos del proyecto.
- No ejecutar operaciones destructivas sobre datos sin autorización explícita.
- No desactivar autenticación/autorización para "probar".
- No exponer datos sensibles en logs.
- Gotcha de negocio: respetar estrictamente la exclusividad de roles y el identificador único de email.
- Gotcha de plazo: las entregas/modificaciones de CU-07 y CU-08 dependen de fecha límite y estado de corrección; validarlo en `services/`, no en el cliente.
