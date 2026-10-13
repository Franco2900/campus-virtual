# Design

## Context

Ver `proposal.md` — Why. El sistema ya tiene las capas `blueprints → services → models`, guards (`@login_required`, `@require_roles`), errores de dominio (`ValidationError`, `NotFoundError`, `ConflictError`, `ForbiddenError`) y el patrón de recurso anidado bajo el curso (`/api/courses/<id>/...`). Existen `Course` (con `active`), `Enrollment` (`UNIQUE(course_id, student_id)`, `active`), `User` (`role`) y `Task` (`active`, `due_date`). Las migraciones Alembic llegan hasta `0005_add_task`. El frontend tiene el design system (`src/ui/`, `src/theme/`) y la feature `tasks/` como referencia del patrón «seleccionar curso → operar sobre sus recursos».

Situación relevante: `GET /api/courses/mine` es hoy Administrador/Profesor (`list_courses_for_user`), y el listado `GET /api/courses/<id>/tasks` es exclusivo del Profesor. El Estudiante no tiene forma de descubrir sus cursos ni de ver las tareas disponibles. CU-06 difirió la vigencia del plazo y la limitación de zona horaria de SQLite a CU-07.

## Goals / Non-Goals

**Goals:**
- Persistir entregas por par (tarea, estudiante) con contenido textual y links.
- Exponer creación, modificación y eliminación de la entrega propia, acotadas al Estudiante, a sus cursos y al plazo.
- Hacer efectiva la vigencia del plazo comparando en UTC normalizado, resolviendo el diferido de CU-06.
- Extender el descubrimiento de cursos y el listado de tareas al rol Estudiante, sin romper los flujos del Profesor/Administrador.
- Construir la pantalla del Estudiante sobre el design system reutilizando el patrón de `tasks/`.

**Non-Goals:**
- Corrección, calificación y retroalimentación (CU-08) y consulta de calificaciones / promedio (CU-09).
- Adjuntos de archivo (se difieren; el modelo queda preparado para incorporarlos por migración).
- La condición «la entrega no fue corregida» del flujo A1: no hay correcciones en CU-07, por lo que se hará efectiva en CU-08 (ver D-K).
- Notificaciones por correo (explícitamente excluidas).
- Listado de entregas de otros estudiantes (pertenece a CU-08).

## Decisions

### D-A: Listado de tareas role-aware en `GET /api/courses/<id>/tasks`
Se reutiliza el mismo recurso («las tareas del curso») y se ramifica por rol: el Profesor sigue recibiendo todas las tareas; el Estudiante recibe únicamente las disponibles y, en cada una, su entrega propia o `null`. Es consistente con `/api/courses/mine` (role-aware) y evita un segundo endpoint para listar tareas. Alternativa considerada: endpoint aparte `/api/courses/<id>/submissions` — rechazada por introducir una segunda URL para el mismo recurso y un nombre ambiguo (devolvería tareas). Requiere modificar el requisito «Alcance de la gestión de tareas» (carve-out del listado) y «Consulta de tareas de un curso».

### D-B: Descubrimiento de cursos del Estudiante vía `GET /api/courses/mine`
Se extiende `course_service.list_courses_for_user` y la autorización del endpoint al rol Estudiante, devolviendo los cursos con **inscripción activa**. Es el mismo contrato que ya usan Profesor/Administrador («cursos sobre los que puedo operar»). Alternativa considerada: endpoint nuevo `/api/courses/enrolled` — rechazada por duplicar el concepto de «mis cursos».

### D-C: Modelo `Submission`
`models/submission.py` con `id`, `task_id` (FK `task.id`, `nullable=False`), `student_id` (FK `user.id`, `nullable=False`), `content` (`Text`, `nullable=False`, default `""`), `links` (`JSON`, `nullable=False`, default lista vacía), `created_at` y `updated_at` (`DateTime(timezone=True)`, default `now(UTC)`), y `UNIQUE(task_id, student_id)` (`uq_submission_task_student`). La cardinalidad es una entrega por par. `links` se guarda como JSON (SQLAlchemy `db.JSON`, soportado por SQLite). **Preparado para adjuntos:** la tabla nueva y la relación 1:N permiten agregar en el futuro una tabla de adjuntos o columnas nullable mediante migración, sin rehacer `Submission`. No se agregan ahora columnas de corrección/calificación (pertenecen a CU-08).

### D-D: Disponibilidad y plazo en UTC normalizado
Una tarea está disponible para el Estudiante si `Task.active` y `Task.due_date` no venció. Como SQLite no preserva el offset de `DateTime(timezone=True)`, al comparar se normaliza: si la fecha leída es naive se interpreta como UTC (`replace(tzinfo=UTC)`) y se compara contra `datetime.now(UTC)`. Crear, modificar y eliminar una entrega exigen la tarea disponible (HTTP 409 si no). El plazo se hace efectivo aquí, cerrando el diferido de CU-06 (D-F). Alternativa considerada: exigir además `Course.active` — rechazada por no figurar entre las precondiciones de CU-07 y por acotar la disponibilidad al estado de la tarea, tal como fijó CU-06.

### D-E: Semántica de los endpoints de entrega
`POST` crea la entrega propia; `PUT` reemplaza `content` y `links` (A1); `DELETE` elimina físicamente (A2). Se anidan bajo `/api/courses/<id>/tasks/<task_id>/submission` porque la autorización depende del curso y la tarea. Es consistente con `enrollments` y `tasks`. Alternativa considerada: `PATCH` parcial — rechazada por alejarse de `PUT`+`PATCH` de cursos/tareas; aquí no hay un subcampo de estado que justifique `PATCH`.

### D-F: Validación del cuerpo (texto y links)
El cuerpo MAY traer `content` (texto, se recorta) y `links` (lista de textos, cada enlace se recorta). MUST haber al menos uno con contenido no vacío (HTTP 400 en caso contrario). Límites: `content` ≤ 5000 caracteres; cada link ≤ 500 caracteres; máximo 10 links. Un `links` que no sea lista de textos o que exceda los límites MUST responder HTTP 400. Alternativa considerada: exigir siempre `content` no vacío — rechazada para admitir entregas basadas sólo en enlaces, coherente con «texto y links».

### D-G: Unicidad y duplicados
`UNIQUE(task_id, student_id)` en el modelo y en la migración. Un `POST` sobre un par con entrega existente MUST responder HTTP 409 (mismo criterio que `enrollment` duplicado). La verificación es sobre la clave lógica del par, no sobre el contenido.

### D-H: Migración Alembic `0006_add_submission`
El esquema se versiona con Flask-Migrate (`flask db migrate` + `upgrade`), no con `db.create_all()` (reservado a tests). Debe registrar `Task`/`Submission` en `app.py` y respetar la paridad modelos↔migraciones que cubre `tests/test_migrations.py`.

### D-I: Orden de validaciones y códigos HTTP
En `services/submission_service.py`, orden: 401 (guard) → 403 rol (guard `STUDENT`) → 404 curso inexistente → 403 Estudiante sin inscripción activa → 404 tarea inexistente o de otro curso → 409 tarea no disponible (inactiva o vencida) → 400 datos → 409 entrega duplicada (solo POST) → 404 entrega inexistente (PUT/DELETE). Los códigos se derivan de las excepciones de dominio reutilizadas. Para el listado role-aware en `task_service`, el orden es 401 → 403 rol inválido → 404 curso → (Profesor) 403 curso ajeno / (Estudiante) 403 sin inscripción.

### D-J: Frontend `features/submissions/` sobre el design system
Nueva feature `src/features/submissions/` (`api.js`, `SubmissionsPage.jsx`, `SubmissionForm.jsx`) con el patrón de `tasks/`: selector de curso vía `GET /api/courses/mine`, tabla de tareas disponibles (`DataTable`) con estado de la entrega, alta/edición en `Modal` con `FormField` (texto + links), eliminación con `ConfirmDialog` (A2) y feedback con `Toast`. Ruta `/submissions` protegida por rol `student` en `App.jsx` e ítem de sidebar. Las validaciones del servidor son la fuente de verdad; el cliente sólo muestra los errores del backend. Los endpoints se documentan como `/api/courses/<id>/tasks/<task_id>/submission`.

### D-K: Condición «no corregida» del flujo A1 diferida a CU-08
El flujo A1 de `casos_de_uso.md` incluye verificar que la tarea no haya sido corregida. En CU-07 no existe corrección (no hay calificación ni estado de corrección), por lo que la condición se satisface trivialmente. CU-08, al introducir la corrección, deberá hacerla efectiva sobre `Submission`. Se documenta como Non-Goal y como riesgo.

## Risks / Trade-offs

- [Extender `GET /api/courses/mine` y `GET /api/courses/<id>/tasks` puede regresar los flujos de Profesor/Administrador] → El comportamiento del Profesor se mantiene idéntico y los tests `test_courses.py`, `test_enrollments.py` y `test_tasks.py` se ejecutan en la verificación.
- [SQLite no preserva el offset de `due_date`] → Se normaliza a UTC al comparar (D-D); los tests cubren fechas en UTC/`Z`. Un `due_date` ingresado con otro offset no se preserva (limitación conocida de CU-06) y se documenta.
- [Adjuntos diferidos] → El modelo queda preparado (tabla nueva + relación 1:N); no hay deuda de esquema más allá de una migración aditiva futura.
- [Condición «no corregida» de A1 sin implementar en CU-07] → Aceptado y documentado (D-K); CU-08 la implementa junto con la corrección.

## Migration Plan

1. Crear la migración `0006_add_submission` (modelo `Submission`) y aplicar `flask db upgrade` sobre la base de desarrollo; en tests el esquema se crea con `create_all()`.
2. Desplegar backend (modelo + servicio + blueprint + ajustes en `course_service`/`task_service`) y luego frontend (feature + ruta).
3. Rollback: `flask db downgrade` elimina la tabla `submission`; no hay datos preexistentes que perder (la tabla es nueva).
