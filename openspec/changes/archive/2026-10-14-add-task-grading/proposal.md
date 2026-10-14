# Proposal

## Why

CU-08 (Corregir tarea) permite al Profesor corregir las entregas realizadas por los estudiantes, asignando una calificación y proporcionando retroalimentación. Hoy no existe la posibilidad de calificar una entrega: el modelo `Submission` solo almacena el contenido y los links de la entrega del estudiante, pero carece de campos para la corrección (`grade`, `feedback`, `graded_at`). Además, CU-07 difirió la verificación de que una entrega no esté ya corregida en el flujo A1 (modificar entrega), ya que dicha restricción depende de que exista el concepto de corrección. CU-08 hace efectiva esa restricción y establece la lógica para determinar el estado aprobado/desaprobado (calificación >= 6).

## What Changes

- **Extensión del modelo `Submission`:** se agregan los campos `grade` (nullable, Integer 1..10), `feedback` (nullable, Text con default vacío) y `graded_at` (nullable, DateTime con timezone). La corrección se identifica porque `grade` es distinto de `null`.
- **Nueva migración Alembic `0007_add_grading`:** versiona el cambio del esquema de `submission`. La tabla mantiene su estructura existente, agregando columnas nullable para no romper datos (no hay datos de corrección preexistentes).
- **Endpoints para corrección (Profesor-only):** 
  - `GET /api/courses/<id>/tasks/<task_id>/submissions` — listar entregas de una tarea con datos del estudiante y estado de corrección (200/403/404)
  - `PUT /api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade` — corregir o modificar una corrección (A1). Body `{"grade": <1..10>, "feedback": "..."}` (200/400/403/404)
- **Promoción automática aprobado/desaprobado:** la calificación >= 6 implica aprobado; 1..5 implica desaprobado. Este estado se deriva de `grade` (no se persiste como columna).
- **Restricción "no corregida todavía":** se modifica el comportamiento de `submission_service.update_submission` y `delete_submission` para rechazar con HTTP 409 las operaciones del Estudiante sobre una entrega que ya tiene `grade` asignada.
- **Frontend (feature `grading`):** nueva página para que el Profesor seleccione curso → tarea → liste entregas → corrija (modal con nota y retroalimentación). Ruta `/grading` protegida por rol `teacher`, ítem en sidebar. Usa el design system existente.
- **No notificaciones por correo:** la corrección no genera envíos automáticos.
- **Preparado para adjuntos futuros:** el modelo queda preparado para adjuntar un archivo corregido (se diferió su implementación por pedido del usuario), sin agregar columnas de archivo ahora.

## Capabilities

### New Capabilities

- **grading-management:** corrección de entregas por parte del Profesor. Incluye listar entregas de una tarea con datos del estudiante y estado de corrección, asignar o modificar una calificación (1..10) con retroalimentación opcional, y la derivación automática de aprobado/desaprobado (nota >= 6). Solo puede operar el Profesor sobre los cursos en los que está asignado. No genera notificaciones por correo.

### Modified Capabilities

- **submission-management:** se agrega la restricción que impide al Estudiante modificar o eliminar su entrega cuando ya está corregida (`grade` no es nulo). La operación debe responder HTTP 409 si la entrega tiene una corrección. Esta regla hace efectiva lo diferido en CU-07 (flujo A1).

## Impact

- **Backend:** extensión de `models/submission.py` (nuevos campos nullable), migración Alembic `0007_add_grading`, nuevo método/ajustes en `services/submission_service.py` (validación "no corregida" en update/delete), nuevo `services/grading_service.py` (lógica de corrección y validaciones), nuevo `blueprints/grading.py` (endpoints Profesor-only), registro del blueprint en `app.py`. Ajustes menores en serialización donde corresponda (sin exponer calificación/retroalimentación en la entrega propia del Estudiante).
- **Frontend:** nueva feature `src/features/grading/` (`api.js`, `GradingPage.jsx`, `GradeSubmissionModal.jsx`) siguiendo el patrón de `tasks/` y reutilizando componentes del design system (`Modal`, `FormField`, `DataTable`, `Toast`, `Button`, `Card`, `PageHeader`). Nueva ruta `/grading` en `App.jsx`, protección por rol `teacher` y nuevo ítem de sidebar.
- **API:** dos nuevos endpoints anidados bajo `/api/courses/<id>/tasks/<task_id>` para el Profesor. No se cambian endpoints de Estudiante existentes, solo se endurece su comportamiento (409 cuando corregida).
- **Datos:** tabla `submission` con nuevas columnas nullable; migración aditiva, sin pérdida de datos.
- **Esquema/versionado:** nueva migración `0007_add_grading` (Flask-Migrate/Alembic). Se respeta la paridad modelos↔migraciones.
