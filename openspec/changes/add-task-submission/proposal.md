# Proposal

## Why

CU-07 (Entregar tarea) es el eslabón que convierte las tareas creadas por el Profesor (CU-06) en trabajo entregable por el Estudiante. Hoy no existe ninguna entidad de entrega: el Estudiante no puede presentar, modificar ni eliminar su trabajo, y sin `Submission` la corrección (CU-08) y las calificaciones (CU-09) no tienen de dónde derivarse. Además, CU-06 difirió explícitamente la vigencia del plazo (`due_date` pasado/futuro) a la entrega, de modo que CU-07 es el punto donde el plazo se hace efectivo y donde se resuelve la limitación de zona horaria de SQLite.

## What Changes

- Nueva entidad de dominio `Submission` (entrega): pertenece a una tarea y a un estudiante, admite **texto y links** (sin archivos por ahora, con el modelo preparado para adjuntos futuros) y tiene cardinalidad **una entrega por par (tarea, estudiante)**.
- Endpoints anidados bajo el curso, restringidos al rol **Estudiante** y sólo sobre cursos en los que está inscripto:
  - el listado de tareas del curso se vuelve role-aware y para el Estudiante incluye su propia entrega.
  - `POST/PUT/DELETE /api/courses/<id>/tasks/<task_id>/submission` para crear, modificar (A1) o eliminar (A2) la entrega propia.
- Regla de disponibilidad y plazo: una tarea está disponible para el Estudiante si está **activa** y su **fecha límite no venció**, comparando en **UTC normalizado** (resuelve la limitación de zona horaria de SQLite diferida desde CU-06). Crear, modificar o eliminar una entrega sólo se permite mientras la tarea esté disponible.
- Extensión de `GET /api/courses/mine` para que el Estudiante obtenga los cursos en los que tiene inscripción activa (hoy sólo Administrador/Profesor).
- Pantalla del Estudiante en el frontend sobre el design system: selección de curso, listado de tareas disponibles con el estado de la entrega y alta/edición/eliminación de la entrega propia.
- Sin notificaciones por correo: la entrega no dispara envíos.

Fuera de alcance (CUs posteriores): la corrección y calificación por el Profesor y la promoción automática aprobado/desaprobado (CU-08), la consulta de calificaciones y el promedio (CU-09) y los adjuntos de archivo.

## Capabilities

### New Capabilities
- `submission-management`: entrega, modificación y eliminación de la entrega propia por parte del Estudiante, restringida a sus cursos y al plazo de la tarea.

### Modified Capabilities
- `enrollment-management`: `GET /api/courses/mine` se extiende al rol Estudiante (cursos con inscripción activa).
- `task-management`: el listado `GET /api/courses/<id>/tasks` pasa a ser role-aware; además del Profesor, el Estudiante obtiene las tareas disponibles con su propia entrega.

## Impact

- **Backend:** nuevo modelo `models/submission.py`, migración Alembic `0006_add_submission`, `services/submission_service.py`, `blueprints/submissions.py` y su registro en `app.py`; ajustes en `course_service.list_courses_for_user` (alcance del Estudiante) y en `task_service`/`blueprints/tasks.py` (listado role-aware).
- **Frontend:** nueva feature `src/features/submissions/` sobre el design system, ruta `/submissions` protegida por rol Estudiante e ítem de sidebar.
- **API:** nuevos endpoints bajo `/api/courses/<id>/tasks/<task_id>/submission` y cambio de alcance de `GET /api/courses/mine` y `GET /api/courses/<id>/tasks` (documentar en `AGENTS.md`).
- **Datos:** nueva tabla `submission` con `FK` a `task` y `user` y `UNIQUE(task_id, student_id)`; sin pérdida de datos existentes.
- **Verificación:** tests `backend/tests/test_submissions.py`, smoke `scripts/smoke_cu07.py` y evidencia UI en `evidencias/cu-07/`.
