# Design

## Context

Ver `proposal.md - Why`. El sistema ya cuenta con las capas `blueprints → services → models`, los guards (`@login_required`, `@require_roles`) y los errores de dominio (`ValidationError`, `NotFoundError`, `ConflictError`, `ForbiddenError`). Piezas reutilizables relevantes:

- `models/task.py`: `Task` con `id`, `course_id`, `title`, `description`, `due_date` (NOT NULL), `active`, `created_at`.
- `models/submission.py`: `Submission` con `grade` (nullable), `feedback` (nullable), `graded_at` (nullable) y `UNIQUE(task_id, student_id)`.
- `models/enrollment.py`: `Enrollment` con `active`, `UNIQUE(course_id, student_id)`.
- `services/grading_service.py`: `serialize_submission(submission, student=None)` (expone `grade`/`feedback`/`graded_at`/`approved`), `APPROVAL_THRESHOLD = 6`, `GRADE_MIN/MAX`.
- `services/course_service.py`: `get_manageable_course(course_id, current_user)` (Profesor asignado, 403 si no; 404 si el curso no existe), `get_course_or_404(course_id)`.
- `services/task_service.py`: `now_utc()` y `as_utc(value)` (normalización de zona horaria para la regla de plazo), `is_task_available(task)`.
- `blueprints/grading.py`: endpoints Profesor-only de corrección (`GET .../submissions`, `PUT .../grade`).
- Frontend: design system (`src/ui/`) y las features `grading/`, `submissions/` como referencia del patrón «seleccionar curso → mostrar recursos»; `App.jsx` con `ProtectedRoute` por rol y `Sidebar.jsx` con ítems por rol.

CU-07 (D-030/D-031) difirió a CU-09 el uso de la entrega/no-entrega para el promedio; CU-08 (D-032/D-033) difirió a CU-09 la visibilidad de `grade`/`feedback` al Estudiante y la consumición del promedio. El endpoint `GET /api/courses/<id>/grades` es nuevo; no existe en el inventario de la API de `AGENTS.md`. **No hay cambio de esquema**: se leen `Task`, `Submission` y `Enrollment`; por lo tanto **no se genera migración**.

## Goals / Non-Goals

**Goals:**
- Exponer un endpoint de solo lectura `GET /api/courses/<id>/grades` que devuelva una vista distinta según el rol (Estudiante o Profesor).
- Calcular el promedio simple según la regla (solo tareas activas; nota si corregida; 1 si venció sin entrega) en la capa `services/`.
- Habilitar de forma deliberada y documentada la visibilidad de `grade`/`feedback`/`graded_at` y del estado derivado al Estudiante, con un serializador específico de esta vista.
- Autorizar por curso: Estudiante con inscripción activa; Profesor asignado (reutilizando `get_manageable_course`).
- Construir la pantalla `/grades` sobre el design system, con guard por rol (Estudiante y Profesor).

**Non-Goals:**
- Modificar el modelo o el esquema (`Submission`/`Task`/`Enrollment` no cambian; sin migración).
- Cambiar los endpoints existentes de corrección (CU-08) o de entrega (CU-07): solo se agrega un endpoint nuevo de lectura.
- Persistir el promedio o el estado aprobado/desaprobado (se derivan en cada consulta).
- Notificaciones por correo; adjuntos de archivos; chatbot; CU-10.
- Definir pesos por tarea u otro criterio de promedio distinto del promedio simple.

## Decisions

### D-A: Un único endpoint role-aware `GET /api/courses/<id>/grades`
Se define un solo endpoint cuya respuesta depende del rol, en lugar de dos endpoints separados (p. ej. `/grades/me` para el Estudiante y `/grades` para el Profesor). Es coherente con el patrón ya existente de listado role-aware (`GET /api/courses/<id>/tasks`, D-031) y con la autorización por curso ya centralizada. Alternativa considerada: dos endpoints — rechazada por duplicar la autorización de curso y fragmentar una misma consulta conceptual («calificaciones del curso según mi rol»).

### D-B: Servicio nuevo `grade_service.py` (consulta), separado de `grading_service.py` (corrección)
La lógica y el armado de las vistas viven en `backend/services/grade_service.py`. `grading_service.py` es del dominio Profesor-only de corrección; mezclar la consulta allí acoplaría dos actores y dos responsabilidades. Se reutilizan `serialize_submission` (como referencia de campos), `get_manageable_course`, `get_course_or_404`, `now_utc` y `as_utc`. Alternativa considerada: extender `grading_service.py` — rechazada por mezclar corrección (escritura, Profesor) con consulta (lectura, ambos roles).

### D-C: Cálculo del promedio en la capa de servicios
El promedio se calcula en `services/` (regla de negocio), nunca en el blueprint ni en el modelo. Se define una función pura, por ejemplo `_counted_value(task, submission)` que devuelve un valor numérico o `None`:
- `task.active` es `False` → `None` (no aporta).
- Existe `submission` con `grade is not None` → `grade`.
- No existe entrega y `now_utc() > as_utc(task.due_date)` (vencida) → `1`.
- En cualquier otro caso → `None` (no aporta); el desglose completo está en D-D.

### D-D: Detalle de la regla del promedio
Para cada tarea activa se calcula su aporte:
1. Si `submission.grade is not None` → aporta `grade`.
2. Si no hay entrega y la tarea venció (`now_utc() > as_utc(task.due_date)`) → aporta `1`.
3. Si la tarea no venció (cualquier estado) → no aporta.
4. Si hay entrega pero no está corregida (`grade is None`) → no aporta (regla «tareas no corregidas no se incluyen»).

El promedio por estudiante es la media aritmética simple de los valores que aportan; si no hay ninguno, es `null`. La comparación de plazo usa la normalización UTC ya establecida (`as_utc`/`now_utc`, D-030 punto 3), porque SQLite no preserva el offset. Nota de redondeo: se devuelve el valor numérico sin redondear (el consumidor formatea); a definir en implementación si se expone con una cantidad fija de decimales.

### D-E: Promedio del curso (Profesor) = media simple de los promedios por estudiante
El promedio del curso se calcula como la media aritmética simple de los promedios de los estudiantes con inscripción activa que tengan al menos un valor que aporte (los estudiantes sin valores no se cuentan). Esto interpreta «promedio del curso … sobre los estudiantes inscriptos» tomando al estudiante como unidad. Alternativa considerada: media simple de todos los valores de la matriz (todas las celdas que aportan), que daría más peso a los estudiantes con más tareas. Queda como **open question** para confirmar antes/durante el apply; ver más abajo.

### D-F: Serializadores separados por vista (visibilidad deliberada al Estudiante)
Se definen dos formas de respuesta:
- **Vista del Estudiante:** `{course, average, tasks:[{task_id, title, due_date, active, submitted, grade, feedback, graded_at, approved, counted, effective_value}]}`. Expone `grade`/`feedback`/`graded_at` y `approved` (`grade >= 6`) cuando la tarea está corregida. Esta es la **decisión explícita de CU-09**: habilitar la visibilidad al Estudiante que CU-08 (D-032.4) difirió. No reutiliza el `_serialize_submission` del blueprint de entregas (que enumera campos y excluye la corrección); se usa un serializador propio.
- **Vista del Profesor:** `{course, tasks:[{task_id, title, due_date, active}], students:[{student:{id, name, email}, grades:{<task_id>: value|null}, average}], course_average}`. Las filas son los estudiantes con inscripción activa y las columnas las tareas activas del curso.

Mantener dos serializadores evita que el endpoint de entrega del Estudiante (CU-07) cambie su contrato y deja explícita la frontera de visibilidad de CU-09. Alternativa considerada: un único serializador compartido — rechazada por acoplar dos formas de respuesta y aflojar la frontera entrega/corrección.

### D-G: Orden de validaciones
`401` (sin sesión, `@login_required`) → `403` (rol no Profesor ni Estudiante, `@require_roles`) → `404` (curso inexistente, `get_course_or_404`) → `403` de alcance por curso (Estudiante sin inscripción activa / Profesor no asignado vía `get_manageable_course`). Este orden replica el patrón ya fijado (D-031/D-033) y mantiene coherencia con `guards.py`.

### D-H: Frontend feature `grades` sobre el design system
Se crea `frontend/src/features/grades/` con `api.js` (`getGrades(courseId)` → `GET /api/courses/<id>/grades`), `GradesPage.jsx` y componentes de vista según el rol. La pantalla usa `GET /api/courses/mine` para el selector de curso (ya devuelve cursos para Profesor y Estudiante). Renderiza:
- **Estudiante:** tabla/cards con las tareas activas (título, estado, nota, retroalimentación) y el promedio del curso destacado.
- **Profesor:** `DataTable` con la matriz estudiante × tarea y el promedio por estudiante / promedio del curso.
Se reutilizan `Card`, `DataTable`, `Badge`/`StatusBadge`, `PageHeader`, `EmptyState`, `Spinner` y `Toast`. Ruta `/grades` en `App.jsx` protegida por rol (`roles={["student", "teacher"]}`) e ítem de sidebar visible para ambos roles. Las validaciones del servidor son la fuente de verdad. Alternativa considerada: dos páginas por rol — rechazada por compartir selector de curso y carga.

### D-I: Sin migración
El cambio no altera el esquema (solo lee datos existentes). No se genera migración Alembic ni se toca `tests/test_migrations.py`.

### D-J: Sin notificaciones
La consulta es de solo lectura y no dispara correos; se documenta explícitamente en la spec.

## Risks / Trade-offs

- **Promedio del curso ambiguo** → Se elige la media de promedios por estudiante (D-E) y se aísla el cálculo en una función del servicio para cambiarlo sin tocar el endpoint si el usuario confirma otra interpretación. Registrado como open question.
- **Visibilidad de la nota al Estudiante** → Cambia la frontera de CU-08 para una vista nueva; se mitiga con un serializador propio y separado del de entregas, de modo que el contrato de CU-07 no se altera.
- **Diferencias de zona horaria** → La regla de «vencida» depende de comparar `due_date` en UTC normalizado (SQLite no preserva el offset); se mitiga reutilizando `as_utc`/`now_utc` de `task_service` (ya validados en CU-07).
- **Cursos sin tareas activas o sin inscriptos** → El promedio puede ser nulo o la matriz vacía; se mitiga definiendo explícitamente el `null` (D-D) y escenarios en la spec, y `EmptyState` en la UI.
- **Estudiantes con inscripción desactivada** → No aparecen en la matriz del Profesor (se filtra por inscripción activa); si el usuario quiere verlos, es un cambio de alcance a confirmar.

## Migration Plan

1. Backend: nuevo `services/grade_service.py` y `blueprints/grades.py`; registrar el blueprint en `app.py`. Sin migración (no hay cambio de esquema).
2. Frontend: nueva feature `src/features/grades/`, ruta `/grades` en `App.jsx` e ítem en `Sidebar.jsx`.
3. Verificación: tests de backend (nuevo `backend/tests/test_grades.py`), suite completa, `npm run build`, smoke HTTP (`scripts/verify.py --cu cu09`) y evidencia UI (Playwright, claro/oscuro).
4. Rollback: revertir los archivos nuevos y el registro del blueprint; no hay datos ni esquema que revertir.

## Open Questions

- **Agregación del promedio del curso (D-E):** ¿media simple de los promedios por estudiante (elegida) o media simple de todos los valores de la matriz? Se asume la primera; confirmar antes o durante el apply. No cambia la estructura del endpoint ni el desglose de tareas (solo el valor `course_average`).
- **Formato del promedio:** ¿se expone con decimales fijos (p. ej. 2) o el número crudo? Se asume número crudo y formateo en el cliente.
- **Alcance de la matriz (Profesor):** se asume incluir solo tareas activas (coherente con la regla del promedio). ¿Debe incluirse también algo de las tareas inactivas como referencia? Se asume que no.
