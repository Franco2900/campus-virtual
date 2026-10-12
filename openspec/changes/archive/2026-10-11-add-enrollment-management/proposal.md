# Proposal

## Why

CU-05 exige que el Administrador y el Profesor gestionen las inscripciones de estudiantes en los cursos, pero hoy el sistema no tiene ninguna entidad de inscripción: no se puede inscribir, modificar ni quitar a un estudiante de un curso. Sin esta entidad, CU-06 a CU-09 (tareas, entregas y calificaciones) no tienen sobre qué estudiantes operar. Además, el flujo del CU requiere que el Profesor vea "los cursos correspondientes", es decir, solo aquellos en los que trabaja, mientras que el listado de cursos existente (`GET /api/courses`) está restringido al Administrador.

## What Changes

- Introducir la entidad `Enrollment` (estudiante↔curso) con estado activo/inactivo (baja lógica) y fecha de inscripción, con unicidad por par curso+estudiante.
- Endpoints de gestión de inscripciones anidados en el curso, habilitados para Administrador y Profesor:
  - `GET /api/courses/mine` — listar los cursos en los que el Profesor trabaja.
  - `GET /api/courses/<id>/students` — listar los estudiantes activos junto con su estado de inscripción en el curso.
  - `POST /api/courses/<id>/students` — inscribir un estudiante (body `{"student_id": <int>}`).
  - `PATCH /api/courses/<id>/students/<student_id>` — modificar la inscripción (activar/desactivar, body `{"active": <bool>}`).
  - `DELETE /api/courses/<id>/students/<student_id>` — eliminar la inscripción (borrado físico del vínculo).
- Alcance por rol: el Administrador opera sobre cualquier curso; el Profesor solo sobre los cursos en los que está asignado (`course_teacher`), con HTTP 403 en caso contrario.
- Validaciones en `services/`: el curso debe existir y estar activo para inscribir/modificar; la cuenta a inscribir debe existir, estar activa y tener rol Estudiante; no se admite una inscripción duplicada (409); operaciones sobre recursos inexistentes responden 404.
- Ajuste de la restricción de `course-management`: `GET /api/courses/mine` es una lectura acotada al Profesor y queda fuera de la regla "solo Administrador" de los endpoints de gestión.
- Frontend: pantalla de gestión de inscripciones (selector de curso, listado de estudiantes con su estado, inscribir/quitar) sobre el design system existente, con ruta protegida para Administrador y Profesor, y visibilidad del ítem de navegación según rol.
- **Fuera de alcance:** filtrado/búsqueda de estudiantes (CU-10); notificaciones por correo (prohibidas por el CU); autogestión de inscripciones por el Estudiante; borrado físico de cursos o usuarios; inscripción masiva/importación.

## Capabilities

### New Capabilities

- `enrollment-management`: gestión de inscripciones de estudiantes en cursos por Administrador y Profesor (listar estudiantes con su estado, inscribir, modificar y eliminar inscripciones) con alcance por rol y reglas de estado del curso.

### Modified Capabilities

- `course-management`: la restricción "solo Administrador" se acota a las operaciones de gestión y listado administrativo, incorporando `GET /api/courses/mine` como lectura acotada al Profesor.

## Impact

- **Backend:** nuevo `backend/models/enrollment.py`; nuevo `backend/services/enrollment_service.py` (listar estudiantes con estado, inscribir, modificar, eliminar) y extensión de la verificación de cursos del Profesor; nuevo `backend/blueprints/enrollments.py` (o extensión de `courses.py`) con los endpoints; registro en `backend/app.py`.
- **Migraciones:** migración incremental `0004` que crea la tabla `enrollment` con `UNIQUE(course_id, student_id)`.
- **Scripts:** nuevo `scripts/smoke_cu05.py`; `scripts/verify.py --cu cu05` y seed de datos de smoke.
- **Tests:** nuevo `backend/tests/test_enrollments.py` (servicio + endpoints + alcance por rol + estados).
- **Frontend:** `src/features/enrollments/` (api + pantalla), ruta `/enrollments` con guard Administrador/Profesor, ítem de navegación en el shell visible para ambos roles.
- **Docs:** `AGENTS.md` (tabla de API, roadmap), `decisiones.md` (modelo de inscripción, alcance por rol, carpeta de endpoints), `README.md`, `progreso.md`, `tiempos.md`, `prompts_log.md`.