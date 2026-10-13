# Design

## Context

Ver `proposal.md` — Why. El sistema ya tiene las capas `blueprints → services → models`, guards de rol (`@login_required`, `@require_roles`), errores de dominio (`ValidationError`, `NotFoundError`, `ConflictError`, `ForbiddenError`) y el patrón de alcance por Profesor `get_manageable_course(course_id, current_user)` implementado en `services/enrollment_service.py` (CU-05). Las migraciones están versionadas con Flask-Migrate/Alembic hasta `0004_add_enrollment`. El frontend ya tiene el design system (`src/ui/`, `src/theme/`) y la feature `enrollments/` como referencia del flujo "seleccionar curso → operar sobre sus recursos" usando `GET /api/courses/mine`.

CU-06 sigue el mismo recorte que CU-05 (recurso anidado bajo el curso), pero cambia el actor: es exclusivamente el Profesor.

## Goals / Non-Goals

**Goals:**
- Persistir tareas por curso con estado activo/inactivo y fecha límite.
- Exponer el CRUD de tareas acotado al Profesor y a sus cursos, con validaciones en `services/`.
- Reutilizar el guard de alcance y los patrones de error existentes, sin duplicar lógica.
- Construir la pantalla de tareas sobre el design system, replicando el patrón de `enrollments/`.

**Non-Goals:**
- Entregas del Estudiante (CU-07), corrección/calificación (CU-08) y consulta de calificaciones (CU-09).
- Enforcement de la vigencia del plazo (pasado/futuro) al entregar: pertenece a CU-07.
- Notificaciones por correo (explícitamente excluidas).
- Gestión de tareas por parte del Administrador (ver Decisión D-B).

## Decisions

### D-A: Endpoints anidados bajo el curso (`/api/courses/<id>/tasks`)
La autorización depende del curso (alcance por Profesor), por lo que el curso debe estar en la ruta igual que en CU-05. Alternativa considerada: endpoints planos `/api/tasks` con `course_id` en el body — rechazada porque obliga a resolver el alcance del curso en cada operación y rompe la consistencia con `enrollments`.

### D-B: Actor exclusivo Profesor
`casos_de_uso.md` define al Profesor como actor principal de CU-06 y la precondición es poseer el rol Profesor. Los endpoints usan `@require_roles(UserRole.TEACHER)`. Alternativa considerada: permitir también al Administrador (como en CU-05) — rechazada por decisión de alcance acordada con el usuario: mantener fidelidad al CU y evitar superficie extra.

### D-C: Modelo `Task`
`models/task.py` con `id`, `course_id` (FK `course.id`, `nullable=False`), `title` (`String(200)`, `nullable=False`), `description` (`String(1000)`, `nullable=False`, default `""`), `due_date` (`DateTime(timezone=True)`, `nullable=False`), `active` (`Boolean`, default `True`), `created_at` (`DateTime(timezone=True)`, default `now(UTC)`). Sin `UNIQUE` adicional: un curso puede tener múltiples tareas y el nombre puede repetirse. Se evita un `due_date` nullable porque la fecha límite es un dato central del CU.

### D-D: Reutilizar `get_manageable_course` moviéndolo a `course_service`
Hoy `get_manageable_course` vive en `enrollment_service`. Para evitar que `task_service` dependa del servicio de inscripciones (acoplamiento entre dominios), se mueve a `services/course_service.py` y `enrollment_service` pasa a importarlo desde allí. Es un refactor de bajo riesgo (mismo comportamiento) que concentra el alcance por curso y responde al señalamiento de `reviews/cu-05.md` (mantener el filtro uniforme en CU-06/CU-08). Alternativa considerada: duplicar la función — rechazada por duplicación de regla de negocio.

### D-E: Semántica `PUT` (reemplazo) vs `PATCH` (estado)
`PUT /api/courses/<id>/tasks/<task_id>` reemplaza `title`, `description` y `due_date`; `PATCH` cambia únicamente `active`. Es consistente con `courses` (PUT + PATCH) y `enrollments` (PATCH para estado). Alternativa considerada: un único PATCH parcial — rechazada por alejarse de los patrones ya aprobados.

### D-F: Validación de `due_date` = fecha válida (sin exigir futuro)
Se exige `due_date` presente y parseable (ISO 8601, tolerando sufijo `Z`), con HTTP 400 si falta o es inválida. No se exige que sea futura: la vigencia del plazo (pasado/futuro) condiciona la entrega y se resuelve en CU-07. Alternativa considerada: rechazar fechas pasadas ya en CU-06 — rechazada por sobre-construir una regla que el propio CU delega a la entrega, y por impedir ajustes legítimos de fecha (flujo A1).

### D-G: Curso inactivo
Crear o modificar tareas exige que el curso esté activo (HTTP 409 si está inactivo, en línea con "los inactivos no se tratan como activos"). El listado, la consulta por id y el cambio de estado de la tarea se permiten aunque el curso esté inactivo (operaciones de lectura o de mantenimiento). Alternativa considerada: bloquear todo sobre cursos inactivos — rechazada porque impide ordenar/desactivar tareas de un curso dado de baja.

### D-H: Migración Alembic `0005_add_task`
El esquema se versiona con una migración generada por Flask-Migrate (`flask db migrate` + `upgrade`), no con `db.create_all()` (reservado a tests). Debe ser idempotente respecto del baseline y consistente con el modelo `Task`.

### D-I: Frontend `features/tasks/` sobre el design system
Nueva feature `src/features/tasks/` (`api.js`, `TasksPage.jsx`, `TaskForm.jsx`) con el mismo flujo que `enrollments/`: selector de curso vía `GET /api/courses/mine`, tabla de tareas (`DataTable`), alta/edición en `Modal` con `FormField`, activar/desactivar con `ConfirmDialog` y feedback con `Toast`. Ruta `/tasks` protegida por rol `teacher` en `App.jsx` + ítem en `Sidebar`. Validaciones del servidor como fuente de verdad (el cliente sólo muestra los errores del backend).

### D-J: Orden de validaciones y errores
En `services/task_service.py`, mismo orden que CU-05: 401 (guard) → 403 rol (guard) → 404 curso inexistente → 403 Profesor no asignado → 409 curso inactivo (solo create/update) → 400 datos → 404 tarea inexistente. Los códigos HTTP se derivan de las excepciones de dominio reutilizadas.

## Risks / Trade-offs

- [Mover `get_manageable_course` puede introducir una regresión en CU-05] → Es un movimiento puro sin cambio de comportamiento; los tests `test_enrollments.py` (31) cubren el alcance 403/404 y se ejecutan en la verificación.
- [El frontend reutiliza `GET /api/courses/mine`, que devuelve también cursos inactivos] → La UI debe deshabilitar el alta/edición cuando el curso está inactivo para reflejar el 409 del backend sin sorpresas; el backend sigue siendo la fuente de verdad.
- [`due_date` sin cota inferior permite tareas ya vencidas] → Aceptado y documentado (D-F); CU-07 es el punto donde el plazo se hace efectivo.

## Migration Plan

1. Crear la migración `0005_add_task` (modelo `Task`) y aplicar `flask db upgrade` sobre la base de desarrollo; en tests el esquema se crea con `create_all()`.
2. Desplegar backend (modelo + servicio + blueprint) y luego frontend (feature + ruta).
3. Rollback: `flask db downgrade` elimina la tabla `task`; no hay datos preexistentes que perder (la tabla es nueva). Las tareas demo de `seed_demo.py` se re-seed con el seed existente.
