# Design

## Context

CU-02 dejó autenticación por cookie firmada y el guard de rol `require_roles` reutilizable (`backend/blueprints/guards.py`), pero el sistema no tiene ninguna entidad de curso ni forma de provisionar un Administrador (CU-01 fuerza rol Estudiante y el guard rechaza todo sin rol admin). Este cambio introduce la primera entidad de dominio gestionada por rol y depende de un bootstrap de administrador para poder operarse y verificarse. Ver proposal.md - Why y specs/course-management/spec.md.

## Goals / Non-Goals

**Goals:**
- Entidad `Course` con nombre, código, descripción, estado activo/inactivo y fecha de creación.
- CRUD de cursos restringido al rol Administrador, reutilizando el guard existente.
- Código único case-insensitive; nombre no único.
- Baja lógica y reactivación (sin borrado físico); el listado incluye inactivos.
- Bootstrap reproducible del Administrador inicial (seed por env) con datos de demo.
- Ruteo en el frontend para sostener vistas por rol.

**Non-Goals:**
- Asignación de profesores al curso: se define en CU-04 (tabla de asociación separada).
- Inscripción de estudiantes al curso (CU-05).
- Borrado físico de cursos.
- Paginación/filtros de listado: el volumen del TP no lo justifica.
- Migraciones formales: tabla nueva cubierta por `db.create_all()` (D-010).

## Decisions

- **D-A — Modelo `Course` y esquema.** Tabla nueva `course` con: `id` (PK), `name` (String 200, NOT NULL), `code` (String 50, NOT NULL, UNIQUE), `description` (String 1000, NOT NULL default `""`), `active` (Boolean, NOT NULL, default `True`), `created_at` (DateTime timezone, default UTC, como `User`). Se crea con `db.create_all()` desde el factory; sin migración porque no hay datos previos que preservar (D-010). Alternativa descartada: introducir Alembic ahora (ceremonia no proporcional; la skill `create-migration` se activará cuando un CU modifique un esquema con datos).
- **D-B — Unicidad de `code` case-insensitive.** El `code` se normaliza a mayúsculas y se recorta al guardar; la columna lleva `UNIQUE`. La verificación previa en `services/` compara el valor normalizado para devolver 409 con mensaje claro en vez de un error de integridad. Alternativa considerada: guardar el `code` tal cual y comparar con `func.lower(...)` (más flexible en casing de presentación, pero un índice único sobre `lower(code)` es menos portable a SQLite y agrega complejidad); se optó por normalizar en el borde.
- **D-C — Endpoints y semántica.** `GET /api/courses` (lista completa, activos e inactivos), `POST /api/courses` (201), `GET /api/courses/<id>` (200/404), `PUT /api/courses/<id>` (200/404/400/409), `PATCH /api/courses/<id>` con body `{"active": <bool>}` (200/404) que cubre desactivar y reactivar. No hay `DELETE`. Todos devuelven el curso serializado (`id`, `name`, `code`, `description`, `active`, `created_at`).
- **D-D — Capas y autorización.** Toda la lógica y validaciones viven en `services/course_service.py`; los `blueprints` solo traducen HTTP ↔ service y aplican `@login_required` + `@require_roles(UserRole.ADMIN)` (guards existentes, sin cambios). El orden de decoradores asegura que `login_required` inyecte `current_user` antes de que `require_roles` evalúe el rol. `course_service` lanza `ValidationError`/`ConflictError`/`NotFoundError` (los errores ya existentes en `services/errors.py`), mapeados a 400/409/404 por el blueprint.
- **D-E — Bootstrap del Administrador inicial (seed).** `scripts/seed_admin.py`, invocable de forma portable (`python scripts/seed_admin.py`, desde la raíz), corre dentro de un `app_context` del factory. Lee `CAMPUS_ADMIN_EMAIL` y `CAMPUS_ADMIN_PASSWORD` (obligatorias; si faltan, termina con error claro y sin tocar la base), reutiliza `generate_password_hash` y crea el `User` con `role=UserRole.ADMIN`. Es idempotente: si el correo ya existe, no duplica ni falla. Además siembra 4 cursos de demo (mezcla de activos e inactivos) para ejercitar el listado y la evidencia. Decidido por el usuario (D-013): seed por script/env en lugar de comando Flask CLI (menos ceremonia y reutilizable para demo/Playwright) o alta manual en la DB (no reproducible).
- **D-F — Frontend: ruteo con `react-router-dom`.** Se introduce `react-router-dom` (decidido por el usuario, D-014) para vistas por rol. `src/App.jsx` monta el `BrowserRouter`, restaura la sesión con `getMe()` y define rutas: `/login`, `/register` (públicas) y `/courses` (solo Administrador), con redirección si no hay sesión o el rol no corresponde. Se agrega `src/features/courses/api.js` (list/create/get/update/setActive sobre `src/api/client.js`) y la pantalla de cursos (listado con estado, alta, edición, activar/desactivar). Alternativa descartada: seguir con render condicional sin router (se vuelve inmanejable a 10 CU con vistas por rol).
- **D-G — Tests.** `backend/tests/test_courses.py` con el cliente de pruebas: 401 sin sesión, 403 con rol no admin, alta válida (201), faltantes (400), código duplicado case-insensitive (409), listado incluye inactivos, consulta/actualización/patch inexistentes (404), patch desactiva/reactiva, y un test del seed (crea admin, login OK, acceso 201; segunda ejecución idempotente; env faltante → error). Se reutilizan los helpers del `conftest.py`.

## Risks / Trade-offs

- [Nueva dependencia de frontend `react-router-dom`] → Autorizada por el usuario; se usa solo para orquestar rutas/vistas por rol, sin rediseñar la arquitectura por feature. Impacto acotado a `App.jsx` y `features/`.
- [Seed con credenciales por env] → Nunca se hardcodean secretos; sin env obligatorias el script falla. El seed no debe usarse en producción sin control; queda documentado como herramienta de arranque/demo.
- [Uso del `require_roles` todavía sin cobertura previa] → El guard existe pero no estaba ejercitado; este CU lo cubre con tests de 403 (Estudiante/Profesor) además del 401.
- [Baja lógica vs. consumidores futuros] → Los CU siguientes (inscripciones, tareas) deberán filtrar por `active` cuando corresponda; se documenta la regla "inactivo no se trata como activo".
- [Idempotencia del seed frente a cambios de contraseña] → Por decisión del usuario, si el admin existe se hace skip silencioso (no se actualiza la contraseña). Limita el uso del seed para rotar credenciales; aceptable.

## Migration Plan

Tabla nueva creada por `db.create_all()` al iniciar el backend (sin migración de datos existentes). Despliegue: ejecutar `scripts/seed_admin.py` con las env del administrador para provisionar la cuenta y los datos de demo. Rollback: quitar los endpoints y el blueprint, y eliminar la tabla `course` (no hay datos productivos que preservar en el TP).

## Open Questions

Ninguna que afecte specs, enfoque o tareas.
