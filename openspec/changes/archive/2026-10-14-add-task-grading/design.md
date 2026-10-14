# Design

## Context

Ver `proposal.md` - Why. El sistema ya cuenta con las capas `blueprints → services → models`, guards (`@login_required`, `@require_roles`) y errores de dominio (`ValidationError`, `NotFoundError`, `ConflictError`, `ForbiddenError`). Existe `Submission` con `task_id`, `student_id`, `content`, `links`, `created_at`, `updated_at` y `UNIQUE(task_id, student_id)`. Las migraciones llegan hasta `0006_add_submission`. El frontend tiene el design system (`src/ui/`, `src/theme/`) y las features `tasks/` y `submissions/` como referencia del patrón «seleccionar curso → operar sobre sus recursos». CU-07 difirió la restricción "no corregida todavía" al momento de modificar/eliminar la entrega del Estudiante; CU-08 hace efectiva dicha restricción e introduce la corrección por parte del Profesor.

## Goals / Non-Goals

**Goals:**
- Extender `Submission` con `grade`, `feedback` y `graded_at` (nullable) sin romper el esquema existente.
- Permitir al Profesor listar entregas de una tarea y corregirlas/modificarlas (calificación 1..10 + retroalimentación opcional).
- Derivar aprobado/desaprobado automáticamente: aprobado si `grade >= 6`, desaprobado si `1 <= grade <= 5` (estado derivado, no persistido).
- Restringir al Estudiante la modificación/eliminación de su entrega cuando ya está corregida (HTTP 409).
- Mantener la corrección sin notificaciones por correo.
- Seguir las convenciones del proyecto (capa services para lógica/validaciones, rutas en blueprints, migración Alembic versionada).
- Desarrollar la UI de corrección sobre el design system reutilizando el patrón de `tasks/`.

**Non-Goals:**
- Exponer calificación o retroalimentación al Estudiante en la entrega propia (eso corresponde a CU-09 según el alcance planteado).
- Implementar adjuntos del archivo corregido (diferido; modelo preparado para migración aditiva futura).
- Calcular promedio o mostrar calificaciones consolidadas al Estudiante (CU-09).
- Modificar el comportamiento de creación de entrega del Estudiante (salvo que la corrección ya exista, pero la creación no tiene esa restricción).

## Decisions

### D-A: Campos de corrección en `Submission`
Se agregan `grade` (Integer, nullable), `feedback` (Text, nullable, default `""`) y `graded_at` (DateTime(timezone=True), nullable). Una entrega no corregida se identifica por `grade is None`. La promoción aprobado/desaprobado se deriva de `grade >= 6`, sin persistir una columna de estado. Alternativa considerada: agregar columna `status` (`CORRECTED`, `PENDING`); rechazada porque es redundante con `grade is None` y agrega complejidad innecesaria. Los campos nullable permiten una migración aditiva sin riesgo para datos existentes.

### D-B: Migración Alembic `0007_add_grading`
Nueva migración `0007_add_grading` que agrega las tres columnas a la tabla `submission`. Se sigue el mismo esquema de versionado usado (`flask db migrate`/`upgrade`). En tests el esquema se crea con `create_all()` (como ya ocurre), por lo que la migración no impacta los tests existentes. Alternativa considerada: modificar migración `0006` — rechazada porque `0006` ya existe/versionada y el esquema debe evolucionar incrementalmente.

### D-C: Servicio `grading_service.py` y capa de servicios
Se crea `backend/services/grading_service.py` con la lógica de corrección: validación de rango 1..10 (entero), validación de feedback con límite (si aplica), verificación de permisos (Profesor asignado al curso vía `get_manageable_course` de `course_service`), verificación de existencia de tarea (pertenece al curso) y verificación de existencia de entrega del estudiante. Esto mantiene la lógica de negocio fuera de blueprints, siguiendo `routes → services → models`. Alternativa considerada: poner validaciones en el blueprint — rechazada por romper la arquitectura establecida.

### D-D: Endpoints anidados bajo curso/tarea
Los endpoints se definen como `GET /api/courses/<id>/tasks/<task_id>/submissions` y `PUT /api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade`. Se anidan bajo la tarea porque la corrección opera sobre las entregas de una tarea específica y la autorización requiere que el Profesor esté asignado al curso. Es consistente con los endpoints de `submissions` existentes. Alternativa considerada: `/api/submissions/<id>/grade` — rechazada porque no aprovecha el patrón anidado bajo curso/tarea y dificulta validar que el Profesor esté asignado al curso correcto.

### D-E: Orden de validaciones
Para ambos endpoints (listar y calificar): 401 (sin sesión) → 403 (rol incorrecto, debe ser TEACHER) → 404 (curso inexistente) → 403 (Profesor no asignado al curso vía `get_manageable_course`) → 404 (tarea inexistente o no pertenece al curso) → luego validaciones específicas (entrega inexistente para calificar, datos inválidos con 400). Este orden replica el patrón usado en CU-07 (D-I) y mantiene coherencia con `guards.py`. Para calificar, se valida además que la entrega existe para el par (tarea, estudiante).

### D-F: Restricción "no corregida" en `submission_service`
En `update_submission` y `delete_submission` (métodos usados por el Estudiante para modificar/eliminar su propia entrega), se agrega una validación: si `submission.grade is not None`, lanzar `ConflictError` con mensaje que indique que la entrega ya fue corregida y no puede modificarse ni eliminarse. Esta validación debe aplicarse **después** de verificar que la tarea está disponible (409 por tarea no disponible) y **antes** o en el contexto adecuado; el orden debe respetar que las validaciones existentes (tarea disponible, contenido válido) se mantienen. Esto hace efectiva la regla diferida de CU-07 sin cambiar el comportamiento de creación.

### D-G: Serialización y visibilidad
La entrega propia del Estudiante (endpoints de `submissions.py`: GET implícito vía listado role-aware, o cualquier serialización usada por el Estudiante) **NO** debe exponer `grade`, `feedback` ni `graded_at`. La serialización usada por el Profesor al listar entregas para corrección **SÍ** debe incluir esos campos (y datos del estudiante). Se mantienen dos vistas/serializadores según el rol/contexto, o se ajusta `_serialize_submission` para no incluir campos sensibles cuando el solicitante es Estudiante. Esto respeta el alcance de CU-08/CU-09 (la visibilidad al Estudiante pertenece a CU-09).

### D-H: Validación de calificación
En el servicio de grading: `grade` debe ser entero y estar entre 1 y 10 inclusive. Se valida el tipo (int o convertible válido). `feedback` es opcional; si se envía, se recorta y respeta un límite de 5000 caracteres (coherente con `content` de CU-07). Ante datos inválidos se retorna HTTP 400 vía `ValidationError`.

### D-I: Frontend feature `grading` sobre design system
Se crea `frontend/src/features/grading/` con `api.js` (llamadas a los dos endpoints), `GradingPage.jsx` (patrón: seleccionar curso vía `GET /api/courses/mine`, seleccionar tarea vía `GET /api/courses/<id>/tasks`, listar entregas con `GET /api/courses/<id>/tasks/<task_id>/submissions`), `GradeSubmissionModal.jsx` (modal con `FormField` para nota 1..10 y retroalimentación). Se reutilizan `DataTable`, `Modal`, `FormField`, `Button`, `Card`, `PageHeader`, `EmptyState`, `Toast` del design system. Ruta `/grading` protegida por rol `teacher` en `App.jsx` e ítem de sidebar. Las validaciones del servidor son la fuente de verdad; el cliente solo muestra errores devueltos por el backend.

### D-J: Sin notificaciones
Tanto en backend (servicio) como en comportamiento, la corrección no genera correos. Esto se documenta explícitamente en los requisitos.

## Risks / Trade-offs

- **Diferido de adjuntos**: El usuario decidió no implementar el archivo corregido ahora. El modelo queda preparado para agregar columnas nullable en una migración futura; no se incurre en deuda estructural relevante.
- **Visibilidad al Estudiante**: Debe tenerse cuidado de no exponer `grade`/`feedback` en serializadores usados por el Estudiante. Esto requiere ajustar `_serialize_submission` o crear un serializador específico para el listado role-aware del Estudiante (CU-07) para asegurar que nunca devuelva esos campos.
- **Actualización de `graded_at`**: Al modificar una corrección existente (A1), `graded_at` debe actualizarse al momento actual (o mantenerse según criterio; el flujo dice "guarda la nueva corrección", por lo que conviene actualizarlo). Se documenta en implementación, pero el spec no lo obliga explícitamente salvo por comportamiento observable.
- **Inscripción del estudiante**: se decidió NO exigir inscripción activa para listar ni corregir. La precondición de CU-08 es solo que exista la entrega; un estudiante cuya inscripción se desactivó después de entregar conserva su entrega y puede ser corregido (evita bloquear la corrección por un cambio de estado administrativo ajeno al trabajo entregado).
- **Rango 1..10 entero**: Debe validarse que `grade` sea entero (no float). En JSON puede venir como número; el servicio debe rechazar valores no enteros.

## Migration Plan

1. Crear migración `0007_add_grading` con columnas nullable (`grade`, `feedback` default `""`, `graded_at` nullable) sobre `submission`.
2. Aplicar migración en base de desarrollo (`flask db upgrade`). En entorno de tests no se aplica (usa `create_all`).
3. Desplegar backend: modelo actualizado, nuevo `grading_service.py`, `blueprints/grading.py` registrado en `app.py`, ajustes en `submission_service.py` (restricción "no corregida").
4. Desplegar frontend: feature `grading` con rutas/protección.
5. Rollback: `flask db downgrade -1` elimina las columnas agregadas (sin pérdida de datos de entregas existentes, ya que son nullable).
