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
- **Backend (dev):** `python backend/app.py` → `http://127.0.0.1:5000`. Base SQLite en `backend/instance/campus.db` (override con `CAMPUS_DB_PATH`; `SECRET_KEY` por entorno).
- **Frontend (dev):** dentro de `frontend/`, `npm install` y `npm run dev` (Windows: `cmd /c npm install`, `cmd /c npm run dev`) → `http://localhost:5173`, con proxy de desarrollo `/api` → `http://localhost:5000`. Build: `npm run build`.
- **Tests (backend):** dentro de `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest`; Linux/macOS `../.venv/bin/python -m pytest`.
- **Lint / formato:** PENDIENTE DE DEFINIR.

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
└── config/           # configuración (DB path, secretos por env)
```

- **Persistencia:** toda consulta a la base se hace desde `services/` a través de los modelos SQLAlchemy. No hay SQL crudo en `routes/`.
- **Validaciones:** en la capa `services/`.
- **Esquema:** SQLite inicializado con `db.create_all()` desde el factory (`create_app()`). Sin migraciones formales todavía (ver D-010); se introducirán (skill `create-migration`) cuando un CU modifique un esquema con datos.
- **Frontend:** organización por feature (`src/features/<feature>/`), con `src/api/client.js` como cliente HTTP base; componentes en `PascalCase`. Las validaciones de servidor son la fuente de verdad: el cliente solo envía y muestra los errores devueltos por el backend.
- **Chatbot:** PENDIENTE DE DEFINIR el punto de integración con LangChain + Ollama.

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
├── prompts_log.md       # auditoría de prompts
├── tiempos.md           # medición de tiempos de desarrollo
├── evidencias/          # screenshots de verificación por CU (evidencia visual)
├── reviews/             # artefactos de revisión por CU (hallazgos, veredicto, mapa de evidencia)
├── backend/             # API Flask (app.py, config/, models/, services/, blueprints/, tests/)
├── frontend/            # SPA React + Vite (src/api/, src/features/)
├── openspec/            # specs spec-driven (openspec): fuente de verdad de specs
├── .atl/
│   └── skill-registry.md  # índice de skills (generado)
└── .opencode/
    ├── agents/          # subagentes: backend, frontend, database, tester, reviewer
    ├── commands/        # comandos /opsx-* del CLI openspec (generados)
    └── skills/          # skills: track-time, new-use-case, create-crud, create-migration, run-verification, openspec-*
```

> No documentar ni referenciar archivos que no existan todavía.

## API

| Método | Ruta | CU | Propósito | Auth |
|--------|------|----|-----------|------|
| POST | `/api/auth/register` | CU-01 | Registrar una cuenta (rol Estudiante) | Público |
| POST | `/api/auth/login` | CU-02 | Iniciar sesión (emite cookie de sesión) | Público |
| GET | `/api/auth/me` | CU-02 | Obtener el usuario autenticado | Sesión |
| POST | `/api/auth/logout` | CU-02 | Cerrar sesión (idempotente; sin sesión responde 200) | Sesión |

> Se completa a medida que se implementan los CU. No inventar endpoints.

## Convenciones

> PENDIENTE DE DEFINIR los detalles. Reglas mínimas ya fijadas:

- **Idioma del código e identificadores:** inglés.
- **Idioma de la documentación (README, AGENTS, docs):** español (neutral).
- **Idioma de la UI y mensajes al usuario:** español (neutral).
- **Backend:** `snake_case` para variables y funciones, `PascalCase` para clases, archivos en `snake_case`.
- **Frontend:** `camelCase` para variables y funciones, `PascalCase` para componentes y sus archivos, archivos de módulos en `camelCase` (p. ej. `client.js`).
- **Comentarios:** ninguno por defecto. Solo cuando expliquen una decisión, restricción o comportamiento no evidente.
- **Indentación / formato:** PENDIENTE DE DEFINIR (esperado: formateador automático).

## Verificación

Comandos reales (verificados en CU-01):

- **Backend:** dentro de `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest`; Linux/macOS `../.venv/bin/python -m pytest`.
- **Frontend:** dentro de `frontend/`, `npm run build` (Windows: `cmd /c npm run build`).
- **Smoke CU-01:** levantar backend y frontend y probar `POST /api/auth/register` (alta 201 + duplicado 409).
- **Smoke CU-02:** `.\.venv\Scripts\python.exe scripts\verify_cu02.py` — arranca backend + Vite, readiness, smoke HTTP completo contra el proxy (login/me/logout/401) y **cleanup garantizado** (detecta puertos ocupados y aborta sin duplicar servicios; mata el árbol de procesos). `--keep` deja los servicios vivos para el smoke UI con Playwright; `--cleanup` detiene los registrados en `scripts/.cu02-pids`.

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

## Portabilidad

- **Objetivo:** el sistema (backend + frontend) debe correr en **Windows, Linux y macOS** con los pasos de "Cómo ejecutar".
- Rutas relativas al proyecto; sin rutas absolutas en el código de la app.
- Sin comandos, separadores ni rutas exclusivos de una plataforma en el código y scripts de la app.
- Documentar los requisitos específicos por SO cuando existan.
- La configuración local de herramientas (p. ej. `opencode.json`: ruta del MCP filesystem y forma del comando) es **tooling específico de la máquina**, no forma parte del sistema portable. No replicar patrones de esa config en el código de la app.

## Roadmap

- **Ahora:** Fase 6 en marcha — **CU-01 (Registrarse) y CU-02 (Autenticarse) implementadas y verificadas** (CU-02: smoke HTTP 10/10 + UI Playwright PASS). Cierre de CU-02 en curso: revisión, archive del cambio `add-user-auth` y commits. Próximo: CU-03.
- **Activo:** pipeline spec-driven por CU vía `new-use-case` (propose → specs → design → tasks → apply → verify → archive) con revisión obligatoria antes de marcar Completo. Nota: el subagente `reviewer` falló por tier del proveedor en CU-01 y CU-02 (ver `errores.md`); se revisa inline con la skill `review-use-case`.
- **Futuro:** plugin de opencode para medir tiempos por tool-call de forma automática.
- **Futuro:** chatbot LangChain + Ollama integrado en la app.
- **Pendiente:** definir lint/formato automático; introducir migraciones cuando un CU cambie el esquema con datos.

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
| `track-time` | Iniciar/cerrar unidades de trabajo y actualizar `tiempos.md` |
| `new-use-case` | Ciclo completo de un CU (planificar e implementar) |
| `create-crud` | Abm/CRUD de una entidad (modelo + servicio + rutas + React) |
| `create-migration` | Cambios de esquema con migraciones |
| `run-verification` | Verificar tests/build antes de declarar algo terminado |
| `review-use-case` | Checklist de revisión de un CU (inline del subagente `reviewer`, con gate de evidencia) |
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
