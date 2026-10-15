# Campus Virtual

Sistema web de gestión académica (campus virtual) con tres roles —Estudiante, Profesor y Administrador— y un asistente conversacional integrado.

Trabajo Práctico Integrador — Curso IA (UNLa) — Grupo 12.

## Vista previa

> PENDIENTE DE DEFINIR: capturas de la aplicación una vez implementada.

## Características

- Registro y autenticación de usuarios (**CU-01 y CU-02 implementados**): alta de cuenta, login con cookie de sesión firmada, sesión actual, cierre de sesión.
- Interfaz con **design system propio**: temas claro/oscuro, color por rol (Estudiante/Profesor/Administrador), componentes reutilizables (`src/ui/`) y animaciones con `motion`.
- Gestión de cursos (**CU-03 implementado**): listado (incluye inactivos), alta, edición y activar/desactivar con baja lógica, restringido al Administrador.
- Gestión de usuarios (**CU-04 implementado**): listado (incluye inactivos), edición de datos y rol, activar/desactivar (baja lógica) y reset de contraseña; asignación de Profesor por curso. Restringido al Administrador.
- Gestión de inscripciones (**CU-05 implementado**): pantalla `/enrollments` para elegir un curso gestionable, ver los estudiantes con su estado de inscripción, inscribir, activar/desactivar y eliminar inscripciones. Disponible para Administrador y Profesor.
- Gestión de tareas (**CU-06 implementado**): pantalla `/tasks` para elegir un curso gestionable, listar las tareas (activas e inactivas), crear, editar (incl. la fecha límite) y activar/desactivar. Disponible para el Profesor.
- Entrega de tareas (**CU-07 implementado**): pantalla `/submissions` para elegir un curso, ver las tareas disponibles con su estado de entrega, entregar (texto y/o links), editar y eliminar con confirmación. Disponible para el Estudiante.
- Corrección de tareas (**CU-08 implementado**): pantalla `/grading` para elegir un curso y una tarea, corregir las entregas con una calificación de 1 a 10 y retroalimentación opcional (máx. 5000 caracteres), ver el estado derivado aprobado/desaprobado y modificar una corrección existente. Disponible para el Profesor.
- Consulta de calificaciones (**CU-09 implementado**): pantalla `/grades` para elegir un curso y ver, como Estudiante, el detalle por tarea (nota, retroalimentación, aprobado/desaprobado) con el promedio del curso; como Profesor, la matriz estudiante × tarea con el promedio de cada estudiante y el promedio del curso.
- Filtrado de usuarios (CU-10).
- Chatbot asistente integrado con LangChain + Ollama.

## Tecnologías

| Área | Tecnología |
|------|-----------|
| Backend | Python + Flask |
| Frontend | React + Vite (Node) |
| Base de datos | SQLite |
| ORM | SQLAlchemy |
| Chatbot | LangChain + Ollama (local) |

Las versiones exactas están en `backend/requirements.txt` (backend) y `frontend/package.json` (frontend).

## Requisitos previos

- Python 3.14 (verificado en 3.14.6) y `pip`.
- Node.js v24 (verificado en v24.19.0) y `npm`.
- En Windows, `npm` se invoca como `cmd /c npm ...` por la execution policy de PowerShell.

## Instalación

```bash
# Backend (desde la raíz del proyecto)
python -m venv .venv
# Windows
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
# Linux/macOS
.venv/bin/python -m pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install        # Windows: cmd /c npm install
```

## Ejecución

```bash
# Backend (desde la raíz) → http://127.0.0.1:5000
.\.venv\Scripts\python.exe backend\app.py   # Windows
.venv/bin/python backend/app.py             # Linux/macOS

# Frontend (desde frontend/) → http://localhost:5173
npm run dev        # Windows: cmd /c npm run dev
```

El servidor de desarrollo de Vite proxea `/api` hacia `http://localhost:5000`.

### Migraciones de esquema

El esquema se versiona con migraciones (Flask-Migrate/Alembic, `backend/migrations/`). Sobre una base nueva o desactualizada hay que aplicar las migraciones pendientes:

```bash
# Desde backend/ (Windows)
..\.venv\Scripts\python.exe -m flask --app app db upgrade
# Linux/macOS: ../.venv/bin/python -m flask --app app db upgrade
```

El seed del Administrador (`scripts/seed_admin.py`) aplica las migraciones pendientes de forma automática antes de sembrar.

## Testing

```bash
# Backend (desde backend/)
..\.venv\Scripts\python.exe -m pytest        # Linux/macOS: ../.venv/bin/python -m pytest

# Frontend (desde frontend/)
npm run build                                 # Windows: cmd /c npm run build

# Lint / formato
python -m ruff check backend && python -m ruff format --check backend   # backend (desde la raíz)
npm run lint:format                           # frontend (desde frontend/)

# Smoke end-to-end (arranca servicios, valida y limpia; por defecto CU-02)
..\.venv\Scripts\python.exe scripts\verify.py                 # Linux/macOS: .venv/bin/python ...
..\.venv\Scripts\python.exe scripts\verify.py --diagnose     # estado de puertos/pids (read-only)
..\.venv\Scripts\python.exe scripts\verify.py --cu cu03      # siembra admin + cursos y corre smoke_cu03
..\.venv\Scripts\python.exe scripts\verify.py --cu cu04      # smoke de gestión de usuarios y profesores
..\.venv\Scripts\python.exe scripts\verify.py --cu cu05      # smoke de gestión de inscripciones
..\.venv\Scripts\python.exe scripts\verify.py --cu cu06      # smoke de gestión de tareas
..\.venv\Scripts\python.exe scripts\verify.py --cu cu09      # smoke de consulta de calificaciones
..\.venv\Scripts\python.exe scripts\verify.py --serve --db backend\instance\campus.db
                                                             # deja backend + Vite vivos y desligados (evidencia UI)
..\.venv\Scripts\python.exe scripts\verify.py --cleanup       # detiene los servicios de --serve/--keep
```

`--serve` levanta los servicios **desligados** del proceso del agente (en Windows con `DETACHED_PROCESS`) y vuelve enseguida, dejando los pids en `scripts/.verify-pids`; es el modo que se usa para capturar evidencia con Playwright. `--cleanup` los detiene (en Windows mata el árbol de procesos).

## Estructura

```
/
├── AGENTS.md          # instrucciones para agentes de IA
├── README.md          # este archivo
├── opencode.json      # configuración de proyecto (MCP, permisos)
├── casos_de_uso.md    # especificación de los 10 casos de uso
├── decisiones.md      # registro de decisiones
├── errores.md         # bitácora de errores
├── progreso.md        # control de progreso
├── docs/              # documentación de soporte (docs/er-diagrama.md: diagrama entidad-relación)
├── openspec/          # specs spec-driven (fuente de verdad de specs)
├── backend/           # API Flask (app.py, config/, models/, services/, blueprints/, migrations/, tests/)
└── frontend/          # SPA React + Vite (src/api/, src/features/, src/theme/, src/ui/, src/app/)
```

## API

| Método | Ruta | CU | Propósito | Auth |
|--------|------|----|-----------|------|
| POST | `/api/auth/register` | CU-01 | Registrar una cuenta (rol Estudiante) | Público |
| POST | `/api/auth/login` | CU-02 | Iniciar sesión (emite cookie de sesión) | Público |
| GET | `/api/auth/me` | CU-02 | Obtener el usuario autenticado | Sesión |
| POST | `/api/auth/logout` | CU-02 | Cerrar sesión (idempotente) | Sesión |
| GET | `/api/courses` | CU-03 | Listar cursos (incluye inactivos) | Sesión + Administrador |
| POST | `/api/courses` | CU-03 | Crear un curso (201/400/409) | Sesión + Administrador |
| GET | `/api/courses/<id>` | CU-03 | Obtener un curso (200/404) | Sesión + Administrador |
| PUT | `/api/courses/<id>` | CU-03 | Editar un curso (200/400/404/409) | Sesión + Administrador |
| PATCH | `/api/courses/<id>` | CU-03 | Activar/desactivar un curso — body `{"active": <bool>}` | Sesión + Administrador |
| GET | `/api/users` | CU-04 | Listar usuarios (incluye inactivos) | Sesión + Administrador |
| GET | `/api/users/<id>` | CU-04 | Obtener un usuario (200/404) | Sesión + Administrador |
| PUT | `/api/users/<id>` | CU-04 | Editar datos y rol (200/400/404/409) | Sesión + Administrador |
| PATCH | `/api/users/<id>` | CU-04 | Activar/desactivar — body `{"active": <bool>}` (200/400/404) | Sesión + Administrador |
| POST | `/api/users/<id>/password` | CU-04 | Resetear contraseña — body `{"password": "..."}` (200/400/404) | Sesión + Administrador |
| GET | `/api/courses/<id>/teachers` | CU-04 | Listar profesores del curso (200/404) | Sesión + Administrador |
| POST | `/api/courses/<id>/teachers` | CU-04 | Asignar profesor — body `{"teacher_id": <id>}` (201/400/404/409) | Sesión + Administrador |
| DELETE | `/api/courses/<id>/teachers/<teacher_id>` | CU-04 | Quitar profesor del curso (200/404) | Sesión + Administrador |
| GET | `/api/courses/mine` | CU-05 | Listar los cursos del usuario (Admin: todos; Profesor: asignados; Estudiante: inscritos) | Sesión + Administrador/Profesor/Estudiante |
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

### Pantallas del frontend (rutas)

| Ruta | Pantalla | Acceso |
|------|----------|--------|
| `/` | Inicio (panel según rol) | Sesión |
| `/login` | Iniciar sesión (CU-02) | Público |
| `/register` | Registrarse (CU-01) | Público |
| `/courses` | Gestión de cursos (CU-03) | Administrador |
| `/users` | Gestión de usuarios (CU-04) | Administrador |
| `/enrollments` | Gestión de inscripciones (CU-05) | Administrador / Profesor |
| `/tasks` | Gestión de tareas (CU-06) | Profesor |
| `/submissions` | Entrega de tareas (CU-07) | Estudiante |
| `/grading` | Corrección de tareas (CU-08) | Profesor |
| `/grades` | Consulta de calificaciones (CU-09) | Estudiante / Profesor |

## Configuración

Variables de entorno (con valores por defecto para desarrollo):

- `CAMPUS_DB_PATH`: ruta del archivo SQLite (default `backend/instance/campus.db`).
- `SECRET_KEY`: clave de sesión (default solo de desarrollo; fijar en producción).
- `CAMPUS_ADMIN_EMAIL`: correo del Administrador inicial (**obligatoria** para el seed).
- `CAMPUS_ADMIN_PASSWORD`: contraseña del Administrador inicial (**obligatoria** para el seed).

### Bootstrap del Administrador

El primer Administrador (y 4 cursos de demostración) se crean con un seed idempotente. Requiere las dos variables `CAMPUS_ADMIN_*`:

```bash
# Windows
$env:CAMPUS_ADMIN_EMAIL="admin@example.com"; $env:CAMPUS_ADMIN_PASSWORD="una-clave-segura"
.\.venv\Scripts\python.exe scripts\seed_admin.py
# Linux/macOS
CAMPUS_ADMIN_EMAIL=admin@example.com CAMPUS_ADMIN_PASSWORD=una-clave-segura .venv/bin/python scripts/seed_admin.py
```

Si el Administrador ya existe, el script no duplica nada. El registro público (`/api/auth/register`) siempre crea rol Estudiante; un Administrador sólo se crea por este seed.

El diagrama entidad-relación de la base (tablas, columnas, restricciones e invariantes de negocio) y cómo poblar datos de prueba están en [`docs/er-diagrama.md`](docs/er-diagrama.md).

## Servidores MCP (Model Context Protocol)

El desarrollo se apoya en tres servidores MCP. La configuración vive en `opencode.json` (proyecto) y en la config global de opencode (`~/.config/opencode/opencode.jsonc`).

| Servidor | Tipo | Origen | Rol en el desarrollo |
|----------|------|--------|----------------------|
| `engram` | Memoria (local) | Config global | Memoria persistente del proyecto: decisiones, gotchas y estado que sobreviven entre sesiones y a la compactación de contexto. |
| `context7` | Documentación (remoto/externo) | Config global | Documentación actualizada de Flask, SQLAlchemy, React, Vite, LangChain y Ollama; reduce APIs alucinadas por el modelo. Es el MCP externo requerido por la consigna. |
| `filesystem` | Filesystem (local) | `opencode.json` (proyecto) | Acceso a archivos acotado por allowlist a la carpeta del proyecto. Valor demostrativo del protocolo; opencode ya dispone de acceso a archivos nativo. |
| `playwright` | Browser e2e (local) | `opencode.json` (proyecto) | Validación real de la UI por CU: navegar, completar formularios y capturar screenshots como evidencia verificable (`@playwright/mcp`, headless + chromium). Complementa, no reemplaza, a pytest y al smoke HTTP. |

- **Terminal:** se resuelve con la herramienta nativa de opencode (no se usa un MCP de terminal, por no existir un servidor oficial maduro).
- **Comando del MCP filesystem:** `cmd /c npx -y @modelcontextprotocol/server-filesystem "<ruta del proyecto>"`.
- **Portabilidad:** la ruta del MCP filesystem es específica de esta máquina. Para correr en otra máquina hay que ajustarla.

## Repositorio

- URL: https://github.com/Franco2900/campus-virtual
- Rama por defecto: `main`. Commits por unidad de trabajo (Conventional Commits). `.atl/` (herramientas locales generadas) está en `.gitignore`.

## Desarrollo spec-driven (openspec)

Los cambios se gestionan spec-driven: cada caso de uso se planifica y se implementa con un pipeline reproducible (propuesta → specs → diseño → tareas → aplicación → verificación → archivo), dejando rastro auditable en `openspec/`.

- Estructura: `openspec/changes/{cambio}/` para cambios activos, `openspec/specs/` como fuente de verdad de specs, `openspec/changes/archive/` como pista de auditoría.
- CLI: `openspec` (invocarlo en Windows como `cmd /c openspec ...` por la execution policy de PowerShell). En opencode se puede usar la vía nativa con los comandos `/opsx-*`.
- `config.yaml` contiene el contexto del proyecto, `strict_tdd` (desactivado hasta que exista un runner de tests) y las reglas por fase.
- Los casos de uso están especificados en `casos_de_uso.md`; openspec los refina por cambio.

## Roadmap

- CU-01 (Registrarse), CU-02 (Autenticarse), CU-03 (Gestionar cursos), CU-04 (Gestionar usuarios), CU-05 (Gestionar inscripciones), CU-06 (Gestionar tareas), CU-07 (Entregar tarea), CU-08 (Corregir tarea) y CU-09 (Consultar calificaciones) implementados end-to-end (backend Flask + frontend React/Vite con ruteo + tests + smoke HTTP y UI con Playwright). El esquema se versiona con migraciones (Alembic).
- Pipeline spec-driven por CU (openspec, orquestado por `new-use-case`).
- Integración completa del chatbot.
- Tests automatizados de frontend.

## Licencia

> PENDIENTE DE DEFINIR.

## Contacto

- Figueroa, Franco Ariel — franco2900@gmail.com — GitHub: Franco2900
