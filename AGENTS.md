# AGENTS.md

Instrucciones persistentes para agentes de IA (opencode) que trabajan en este proyecto.
Este archivo es la fuente de verdad compartida. El README es para humanos.

## Proyecto

- **Nombre:** Campus Virtual.
- **Propósito:** sistema web completo (backend + frontend) que gestiona cursos, usuarios, inscripciones, tareas y calificaciones con tres roles (Estudiante, Profesor, Administrador) y un chatbot integrado.
- **Contexto:** Trabajo Práctico Integrador (UNLa), Grupo 12. El foco de evaluación es la orquestación de AI Engineering y la funcionalidad, no la estética.
- **Componentes:** backend Flask (API REST), frontend React + Vite, base SQLite vía SQLAlchemy, chatbot LangChain + Ollama local.

## Contexto por dominio — cargar bajo demanda

Este archivo describe el contrato compartido. El detalle de cada capa NO se carga por defecto:

| Necesitás | Leer antes |
|---|---|
| Tocar `backend/` | `backend/AGENTS.md` |
| Tocar `frontend/` | `frontend/AGENTS.md` |
| Un endpoint o el cliente HTTP | `docs/api.md` |
| Estado histórico y métricas por CU | `progreso.md` |
| Detalle de un caso de uso | `casos_de_uso.md` |

Regla: cargar solo lo que la tarea necesita. No precargar la tabla entera.

## Cómo ejecutar

En Windows, `npm` y `openspec` se invocan con el prefijo `cmd /c` por la execution policy de PowerShell (D-006); en Linux/macOS se omiten el prefijo y los sufijos `.exe`. Los comandos por capa están en el `AGENTS.md` de cada dominio.

- **Entorno (una vez, desde la raíz):** `python -m venv .venv`; instalar con Windows `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt` / Linux-macOS `.venv/bin/python -m pip install -r backend/requirements.txt`.
- **Backend (dev):** Windows `.\.venv\Scripts\python.exe backend\app.py` / Linux-macOS `.venv/bin/python backend/app.py` → `http://127.0.0.1:5000`. Base SQLite en `backend/instance/campus.db` (override `CAMPUS_DB_PATH`; `SECRET_KEY` por entorno).
- **Frontend (dev):** dentro de `frontend/`, `npm install` y `npm run dev` → `http://localhost:5173`, con proxy `/api` → `http://localhost:5000`.
- **Migraciones:** desde `backend/`, Windows `..\.venv\Scripts\python.exe -m flask --app app db upgrade` / Linux-macOS `../.venv/bin/python -m flask --app app db upgrade` (D-023).
- **Tests:** dentro de `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest` / Linux-macOS `../.venv/bin/python -m pytest`.
- **Lint/formato:** backend desde la raíz con `ruff` (Windows `.\.venv\Scripts\python.exe -m ruff` / Linux-macOS `.venv/bin/python -m ruff`); frontend con `npm run lint:format` dentro de `frontend/`.

## Arquitectura

- **Patrón:** capas + Blueprints por dominio (Flask).
- **Regla de dependencias:** `routes → services → models`. La lógica de negocio vive en `services/`, nunca en `routes/` ni en los modelos.
- **Persistencia:** las consultas pasan por `services/` usando los modelos SQLAlchemy. Sin SQL crudo en `routes/`.
- **Validaciones:** en `services/`. Las del servidor son la fuente de verdad; el cliente solo envía y muestra los errores que devuelve el backend.
- **Frontend:** organización por feature (`src/features/<feature>/`), `src/api/client.js` como cliente HTTP base, componentes en `PascalCase`, UI sobre un design system propio con tema claro/oscuro (D-019/D-020). Detalle en `frontend/AGENTS.md`.
- **Chatbot (CU-11, D-039/D-040):** agente LangChain + Ollama local en `backend/services/chat_service.py`; historial en `conversation`/`message`; herramientas de solo lectura scopeadas por la sesión del usuario. Fallo de Ollama → 502 y el turno no se persiste.
- **Fuentes de conocimiento (CU-12, D-044..D-047):** administración exclusiva del Administrador; herramienta `search_knowledge_sources` con ChromaDB + embeddings de Ollama. Requiere `ollama pull nomic-embed-text`.
- **Rutas y estructura completas:** `backend/AGENTS.md` y `frontend/AGENTS.md`.

## API

Contrato completo por endpoint (método, ruta, CU, propósito, auth y códigos) en `docs/api.md`. Leerlo antes de tocar un endpoint o el cliente HTTP.
Regla: no inventar endpoints. Se completa a medida que se implementan los CU.

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
| CU-12 | Gestionar fuentes de conocimiento del chatbot | Administrador |

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
├── AGENTS.md            # contrato compartido (este archivo)
├── README.md            # documentación para humanos
├── casos_de_uso.md      # especificación de los CU
├── progreso.md          # control de progreso e histórico por CU
├── decisiones/          # decisiones: README.md (índice) + 00-general.md + cu-0X.md
├── errores/             # bitácora de errores: README.md + 00-general.md + cu-0X.md
├── evidencias/          # screenshots de verificación por CU
├── reviews/             # artefactos de revisión por CU
├── docs/                # api.md (contrato de API), er-diagrama.md
├── scripts/             # verify.py, seed_admin.py, seed_demo.py, smoke_cu0X.py
├── backend/             # API Flask — ver backend/AGENTS.md
├── frontend/            # SPA React + Vite — ver frontend/AGENTS.md
├── openspec/            # specs spec-driven: fuente de verdad
├── .atl/                # índice de skills (generado, local a la máquina)
└── .opencode/           # agents/ (backend, frontend, database, tester, reviewer), commands/, skills/
```

> No documentar ni referenciar archivos que no existan todavía.

## Convenciones

- **Idioma del código e identificadores:** inglés.
- **Idioma de la documentación (README, AGENTS, docs):** español (neutral).
- **Idioma de la UI y mensajes al usuario:** español (neutral).
- **Backend:** `snake_case` para variables y funciones, `PascalCase` para clases, archivos en `snake_case`.
- **Frontend:** `camelCase` para variables y funciones, `PascalCase` para componentes y sus archivos, archivos de módulos en `camelCase` (p. ej. `client.js`).
- **Comentarios:** ninguno por defecto. Solo cuando expliquen una decisión, restricción o comportamiento no evidente.
- **Indentación / formato:** `ruff format` (Python) y `Prettier` (JS/JSX), configuración en `backend/pyproject.toml` y `frontend/.prettierrc`.

## Verificación

- **Backend:** dentro de `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest`; Linux/macOS `../.venv/bin/python -m pytest`.
- **Frontend:** dentro de `frontend/`, `npm run build` (Windows: `cmd /c npm run build`).
- **Smoke HTTP general:** `.\.venv\Scripts\python.exe scripts\verify.py [--cu CU-0X]` — arranca backend + Vite, readiness, corre el smoke del CU contra el proxy y hace cleanup garantizado (detecta puertos ocupados y aborta sin duplicar servicios; mata el árbol de procesos). `--keep` deja los servicios vivos para el smoke UI con Playwright; `--cleanup` los detiene; `--diagnose` muestra en solo lectura puertos y pids registrados.
- **Servicios vivos para evidencia UI:** `.\.venv\Scripts\python.exe scripts\verify.py --serve [--db backend\instance\campus.db] [--seed-demo]` — levanta backend + Vite desligados del proceso del agente, espera el readiness y retorna en segundos dejando los pids en `scripts/.verify-pids`. **Gotcha:** lanzar los servicios en primer plano desde el shell del agente mantiene abierto el árbol de procesos y el tool call no retorna nunca; usar siempre `--serve` (ver `errores/00-general.md`).

- No declarar una tarea completada sin haber ejecutado su verificación.
- Conservar mensajes de error completos.
- Un CU se considera Completo solo cuando: funcionalidad implementada, código ejecutando, tests ejecutados, documentación y `progreso.md` actualizados.

## Evidencia y revisiones

- Screenshots por CU en `evidencias/cu-0X/` con nombres estandarizados `NN-accion.png` (full-page cuando aporte), cada uno ligado a un paso probado.
- Cada cierre de CU persiste `reviews/cu-0X.md`: hallazgos con `archivo:línea`, severidad (Bloqueante/Alta/Media/Baja), veredicto (APROBADO/RECHAZADO) y mapa de evidencia.
- Gate de evidencia: los screenshots deben mostrar el estado esperado (o salida real de smoke/tests si el CU no es visual) y la consola no debe tener errores inesperados.
- La revisión se ejecuta con el subagente `reviewer`; si no está disponible, con la skill `review-use-case` inline.

## Progreso visible (heartbeat)

- Reportar avance en cada turno: qué se está haciendo, qué sigue y estado de la todo list. No dejar pasajes largos sin salida al usuario.
- Antes de un tool call largo (tests, build, subagente): avisar qué se ejecuta y la duración estimada; si supera ~2-3 min sin salida, reportarlo explícitamente.
- Partir tareas grandes en pasos cortos y verificables, con su verificación en cada paso; mantener la todo list actualizada en tiempo real.
- Delegar en subagentes trabajo acotado y sin tramos silenciosos; si hay pasos largos, exigir reportes intermedios.
- Commitear por unidad de trabajo concluida para preservar avance y marcar hitos (skill `work-unit-commits`).

## Fases y sesiones

- Trabajar **un CU por fase** y, en lo posible, **una sesión por CU**.
- Señales para abrir sesión nueva: contexto cargado o degradado, cierre de un CU (después del archive y los commits) y arranque de un CU nuevo.
- Protocolo de cierre: commitear la unidad en curso, ejecutar `mem_session_summary` con el estado completo, cerrar y abrir sesión nueva; al retomar, cargar `mem_context`/`mem_search`, leer de `progreso.md` solo la sección del CU activo y continuar.

## Optimización de tokens

- **Tests acotados:** en iteración correr solo los tests del dominio (`-m pytest tests/test_tasks.py -q`); el suite completo (`-m pytest`) y el build/lint solo en el gate de cierre del CU.
- **Salida acotada:** pytest con `-q`; no imprimir salidas de éxito largas ni logs completos; si la salida es enorme, grep sobre el archivo capturado.
- **Retomar sin releer todo:** cargar `mem_context`/`mem_search` y leer de `progreso.md` solo la sección del CU activo; no releer `AGENTS.md` a mano (el runtime ya lo inyecta).
- **Playwright quirúrgico:** si un paso de evidencia falla, re-capturar solo las pantallas afectadas, no el flujo completo.
- **Delegar el "¿qué cambió?":** si comprender el sprint anterior requiere leer 4+ archivos, delegar el resumen del diff (~10 líneas) a un subagente en vez de llenar el contexto del orquestador.

## Portabilidad

- El sistema debe correr en Windows, Linux y macOS con los pasos de "Cómo ejecutar".
- Rutas relativas al proyecto; sin rutas absolutas ni comandos exclusivos de una plataforma en el código y scripts de la app.
- La configuración local de herramientas (`opencode.json`: ruta del MCP filesystem, forma del comando) es tooling de la máquina, no parte del sistema portable. No replicar esos patrones en el código.

## Estado del proyecto

Alcance CU-01..CU-12 implementado, verificado y archivado. Histórico por CU, métricas de tests, smokes, revisiones y deuda técnica en `progreso.md`; no se replica acá.

## Límites

- No reemplazar tecnologías ni versiones del stack sin autorización.
- No introducir dependencias nuevas si ya existe una adecuada.
- No rediseñar la arquitectura existente por preferencia personal.
- No implementar funcionalidad fuera del alcance de los CU.
- No tocar archivos marcados como generados (cuando existan).

## MCP y herramientas

- **engram** (memoria, local): memoria persistente del proyecto. No reemplaza a `decisiones/`/`progreso.md`.
- **context7** (docs, remoto): consultar documentación actualizada antes de escribir código de librerías (Flask, SQLAlchemy, React, Vite, LangChain). Evita APIs inventadas.
- **filesystem** (local, `opencode.json`): acceso acotado por allowlist. Valor demostrativo.
- **playwright** (UI e2e, local): navegar, completar formularios y capturar screenshots como evidencia por CU (D-012). Requiere instalar el browser.
- **github** (remoto, solo lectura): inspeccionar issues, PRs y runs de Actions. No forma parte del flujo de entrega por CU.
- **openspec CLI** (spec-driven): invocar siempre `cmd /c openspec ...` en Windows (D-006). Los comandos `/opsx-*` omiten esa complejidad.
- Requisito de la consigna: mínimo 2 servidores MCP, al menos 1 externo (engram + context7 + filesystem).

## Skills y subagentes

Skills del proyecto (`.opencode/skills/`, registradas en `.atl/skill-registry.md`):

| Skill | Cuándo |
|-------|--------|
| `new-use-case` | Ciclo completo de un CU |
| `create-crud` | CRUD de una entidad (modelo + servicio + rutas + React) |
| `create-migration` | Cambios de esquema con migraciones |
| `run-verification` | Verificar tests/build antes de declarar algo terminado |
| `review-use-case` | Checklist de revisión de un CU |
| `design-system` | UI sobre `src/ui/` + tokens + shell + `motion` |
| `openspec-*` (6) | Vía nativa del CLI: propose, explore, update-change, apply-change, sync-specs, archive-change |

Subagentes (`.opencode/agents/`): `backend`, `frontend`, `database`, `tester`, `reviewer` (read-only). El `reviewer` es obligatorio antes de marcar un CU como Completo; si no está disponible, ejecutar la skill `review-use-case` inline.

- El subagente `backend` trabaja sobre `backend/` y su contrato está en `backend/AGENTS.md`.
- El subagente `frontend` trabaja sobre `frontend/` y su contrato está en `frontend/AGENTS.md`.

Recomendar skills y subagentes nuevos cuando un patrón se repita; no crear por cumplir inventario.

## Seguridad y gotchas

- **Nunca** escribir secretos, tokens ni credenciales en el código; usar variables de entorno.
- **Nunca** almacenar credenciales en archivos del proyecto.
- No ejecutar operaciones destructivas sobre datos sin autorización explícita.
- No desactivar autenticación/autorización para "probar".
- No exponer datos sensibles en logs.
- Gotcha de negocio: respetar la exclusividad de roles y el identificador único de email.
- Gotcha de plazo: las entregas/modificaciones de CU-07 y CU-08 dependen de fecha límite y estado de corrección; validarlo en `services/`, no en el cliente.
