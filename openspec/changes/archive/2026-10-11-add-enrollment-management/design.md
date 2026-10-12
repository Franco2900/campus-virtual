# Design

## Context

Ver `proposal.md - Why` y `specs/enrollment-management/spec.md`. El proyecto ya tiene: separación `routes → services → models` con validaciones en `services/` y errores tipados (`services/errors.py` → `ValidationError` 400, `ConflictError` 409, `NotFoundError` 404); guards `@login_required` + `@require_roles` (`backend/blueprints/guards.py`); relación profesor↔curso (`course_teacher`, CU-04); patrón de subrecurso anidado (`/api/courses/<id>/teachers`); migraciones Alembic (`backend/migrations/`, última revisión `0003`); design system de frontend con shell por rol. No existe aún una entidad de inscripción ni una forma de que un Profesor vea sus cursos.

## Goals / Non-Goals

**Goals:**
- Entidad `enrollment` (estudiante↔curso) con baja lógica y unicidad por par.
- Endpoints anidados de gestión de inscripciones para Administrador y Profesor, con alcance por rol.
- Lectura `GET /api/courses/mine` acotada al alcance de gestión (Profesor: asignados; Admin: todos).
- Validaciones de negocio en `services/` (curso activo, cuenta estudiante activa, duplicados).
- Migración incremental `0004` y cobertura de tests del backend.
- Pantalla de inscripciones sobre el design system, con ruta y navegación por rol.

**Non-Goals:**
- Filtrado/búsqueda de estudiantes (CU-10).
- Notificaciones por correo (explícitamente prohibidas por el CU).
- Autogestión del Estudiante (inscribirse solo); la operación es de Admin/Profesor.
- Inscripción masiva/importación.
- Borrado lógico como única vía: "eliminar" del CU es borrado físico del vínculo.

## Decisions

- **D-A — Modelo `Enrollment`.** Nueva tabla `enrollment`: `id` (PK), `course_id` (FK→`course.id`, NOT NULL), `student_id` (FK→`user.id`, NOT NULL), `active` (Boolean, NOT NULL, default `True`), `enrolled_at` (DateTime UTC, NOT NULL, default `now(UTC)`) y `UNIQUE(course_id, student_id)`. Razón: el CU pide "registrar, modificar o eliminar"; "modificar" se resuelve como activar/desactivar (baja lógica, consistente con `course.active` y `user.active`) y "eliminar" como borrado físico del vínculo. Alternativa descartada: vínculo plano sin estado (no soporta "modificar" sin eliminar y recrear, y pierde la fecha de inscripción).
- **D-B — Rutas y blueprints.** Los endpoints de inscripciones viven en un blueprint nuevo `blueprints/enrollments.py` con `url_prefix="/api/courses"` y rutas `/<int:course_id>/students[...]` (coherente con `/teachers` y con el flujo del CU: se selecciona primero el curso). `GET /api/courses/mine` se implementa en `blueprints/courses.py` (ya tiene la serialización de curso) con `@login_required` + `@require_roles(UserRole.ADMIN, UserRole.TEACHER)`. Razón: AGENTS.md define blueprints por dominio (auth, courses, users, tasks, enrollments, grades). Alternativa descartada: todo dentro de `courses.py` (mezcla dos dominios y engorda el blueprint).
- **D-C — Error de autorización en `services/`.** Se agrega `ForbiddenError` a `services/errors.py`; las rutas lo mapean a HTTP 403. Se usa para el Profesor que intenta operar sobre un curso en el que no trabaja. Razón: la regla de negocio "un Profesor solo opera sobre los cursos en los que trabaja" se valida en `services/` (regla de negocio), mientras `require_roles` queda para el 403 de rol. Alternativa descartada: devolver 404 para ocultar la existencia del curso; se optó por 403 porque el CU exige la restricción explícita y el contexto es un campus autenticado.
- **D-D — Orden determinista de validaciones.** En cada operación: (1) guard: 401 sin sesión, 403 por rol; (2) curso existente → 404; (3) Profesor asignado al curso → 403 `ForbiddenError`; (4) curso activo en POST/PATCH → 409; (5) para POST: estudiante existente → 404, activo y con rol Estudiante → 400, duplicado (activa o inactiva) → 409. Razón: códigos predecibles y testeables; misma prioridad en todos los endpoints.
- **D-E — Semántica de las operaciones.** `POST` crea la inscripción activa y NO hace upsert: si existe una fila (activa o inactiva) responde 409, incluso con `IntegrityError` como red de seguridad (patrón `course_teacher`). `PATCH` con `{"active": <bool>}` exige booleano (400 si falta o no es booleano) y 404 si no existe la inscripción. `DELETE` es físico y permitido aunque el curso esté inactivo (limpieza), con 404 si no existe. Razón: la reactivación explícita por PATCH mantiene el "modificar" visible en la UI y evita efectos colaterales ocultos en el alta. Alternativa descartada: POST con reactivación implícita (confunde alta con modificación y dificulta el testeo del 409).
- **D-F — Listado de estudiantes.** `GET /api/courses/<id>/students` devuelve las cuentas **activas** con rol Estudiante, ordenadas por `id`, cada una con `enrollment`: `null` si no tiene inscripción, o `{id, active, enrolled_at}` (ISO 8601) si la tiene (activa o inactiva). Razón: el paso 4 del flujo ("muestra los estudiantes y sus inscripciones") y la UI necesitan distinguir "sin inscripción" de "inscripción inactiva" para ofrecer inscribir / activar / desactivar / eliminar sin llamadas extra. Las cuentas inactivas no se listan aunque tengan inscripción (una cuenta dada de baja no opera); su inscripción persiste y reaparece si la cuenta se reactiva. Asunción registrada.
- **D-G — `GET /api/courses/mine`.** Para Profesor devuelve los cursos con `JOIN course_teacher` (incluye inactivos, para que la UI muestre el estado y deshabilite acciones); para Administrador devuelve todos los cursos (misma consulta que el listado admin). Orden por `id`. Serialización idéntica a `_serialize_course`. Razón: es "el sistema muestra los cursos correspondientes" del paso 2 del CU; un Admin gestiona todos. Alternativa descartada: parametrizar `GET /api/courses` con scope (rompe la semántica admin-only del endpoint existente y su spec).
- **D-H — Migración `0004`.** `flask db migrate -m "add enrollment"` tras implementar el modelo genera `CREATE TABLE enrollment` con su unique constraint y FKs; `flask db upgrade` la aplica a la base real y a la temporal de `scripts/verify.py` (que ya aplica migraciones antes del seed). Los tests siguen creando el esquema con `db.create_all()` (modo `TESTING`); el test de paridad modelos↔migraciones existente cubre la tabla nueva. Rollback: `flask db downgrade 0003` (drop de la tabla). Razón: patrón adoptado en CU-04 (D-023); la tabla es nueva, sin datos que preservar.
- **D-I — Frontend.** Feature `src/features/enrollments/` (`api.js`, `EnrollmentsPage.jsx`) con selector de curso alimentado por `GET /api/courses/mine`, tabla de estudiantes (`DataTable`) con `Badge` de estado y acciones: Inscribir (POST), Activar/Desactivar (PATCH), Eliminar (DELETE, vía `ConfirmDialog`), con `Toast` de resultado. `ProtectedRoute` se extiende para aceptar `roles` (array), manteniendo compatibilidad con `role` (string) existente. Ruta `/enrollments` y ítem de sidebar visible para `admin` y `teacher`. Los errores del backend se muestran tal cual (cliente sin validación propia). Razón: skill `design-system` y convenciones de features; la UI debe ser usable por ambos roles con el mismo componente.
- **D-J — Tests.** Nuevo `backend/tests/test_enrollments.py`: servicio y endpoints cubriendo 401/403 (rol y Profesor no asignado), 404 (curso/estudiante), 409 (duplicado, curso inactivo), 400 (cuenta no estudiante/inactiva, `active` inválido), alta/modificación/eliminación exitosa, listado con y sin inscripción, y `GET /api/courses/mine` para Profesor (asignados/vacío) y Admin (todos). Smoke `scripts/smoke_cu05.py` end-to-end vía proxy con Profesor y Admin. Razón: cada escenario de la spec es un caso de test; el smoke cubre el camino observable por HTTP.
- **D-K — Sin notificaciones.** No existe mecanismo de correo en el sistema; la spec lo fija como requisito negativo y no hay código que agregar. Se documenta para trazabilidad del CU.

## Risks / Trade-offs

- [Cuentas inactivas con inscripción] → No aparecen en el listado (D-F) pero su inscripción persiste; si la cuenta se reactiva, la inscripción reaparece. Aceptable y documentado; evita mostrar cuentas que no pueden operar.
- [403 del Profesor revela que el curso existe] → El CU exige "no puede operar en cursos donde no trabaja" y el contexto es autenticado; se acepta el 403 explícito sobre el 404 encubierto.
- [Carrera de duplicados] → El `UNIQUE(course_id, student_id)` es la garantía final; `IntegrityError` se captura y se traduce a 409 (patrón `course_teacher`).
- [Cursos inactivos] → POST/PATCH responden 409; DELETE se permite para limpieza. La UI deshabilita inscribir/activar en cursos inactivos y lo indica con un `Badge`.
- [Extensión de `ProtectedRoute`] → Se preserva `role` (string) como contrato existente y se agrega `roles` (array); las pantallas actuales no se tocan.
- [Drift modelos↔migraciones] → El test de paridad existente falla si la migración `0004` no refleja el modelo `enrollment`.
- [Profesor sin cursos] → `/mine` responde 200 con lista vacía; la UI muestra `EmptyState` ("no tenés cursos asignados") sin error.

## Migration Plan

1. Implementar `backend/models/enrollment.py` y registrarlo en `app.py`.
2. `flask db migrate -m "add enrollment"` → revisión `0004` (`CREATE TABLE enrollment`).
3. `flask db upgrade` sobre `backend/instance/campus.db` y sobre la base temporal de `scripts/verify.py`.
4. Entornos nuevos: `flask db upgrade` construye todo desde cero.

Rollback: `flask db downgrade 0003` elimina la tabla `enrollment`. Sin datos productivos que preservar fuera del TP.

## Open Questions

Ninguna que afecte specs, enfoque o tareas.