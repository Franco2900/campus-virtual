# Proposal

## Why

CU-09 (Consultar calificaciones) permite que el Estudiante consulte las notas y la retroalimentación de sus tareas y que el Profesor consulte las calificaciones de los estudiantes de sus cursos, con el promedio calculado según las reglas. Hoy no existe ninguna vía de consulta de calificaciones: CU-08 persiste `grade`/`feedback`/`graded_at` en `Submission` pero deliberadamente **no** los expone al Estudiante (D-032.4), y no hay un endpoint consolidado de calificaciones. CU-09 es el caso de uso donde se habilita la visibilidad del Estudiante y se formaliza el cálculo del promedio (promedio simple; tareas no corregidas fuera del promedio; tareas no entregadas fuera de plazo contadas como 1). CU-07 y CU-08 difirieron explícitamente a CU-09 tanto la visibilidad de la nota como el uso de la entrega/no-entrega para el promedio.

## What Changes

- **Nuevo endpoint de consulta de calificaciones (role-aware):** `GET /api/courses/<id>/grades` con `@login_required` + `@require_roles(UserRole.TEACHER, UserRole.STUDENT)`. La respuesta depende del rol y se autoriza por curso (Estudiante con inscripción activa; Profesor asignado al curso).
- **Vista del Estudiante:** detalle por tarea (nota y retroalimentación cuando está corregida) y el promedio del curso. El Estudiante solo consulta sus propias calificaciones.
- **Vista del Profesor:** matriz estudiante × tarea de los estudiantes inscriptos en el curso y el promedio del curso.
- **Regla de promedio (promedio simple):** se calcula solo sobre las tareas **activas** del curso. Cada tarea activa aporta su nota si está corregida, o **1** si su `due_date` ya venció y no hubo entrega. Las tareas inactivas y las que aún no vencieron quedan fuera del cálculo; las tareas no corregidas no se incluyen.
- **Visibilidad de la corrección al Estudiante:** a diferencia de CU-08, la vista del Estudiante sí expone `grade`/`feedback`/`graded_at` y el estado aprobado/desaprobado derivado (`grade >= 6`). Este cambio de visibilidad es una decisión deliberada y documentada del alcance de CU-09.
- **Nuevo serializador específico de calificaciones:** la vista del Estudiante no reutiliza el serializador de entrega; se define una forma de respuesta propia de consulta.
- **Frontend (feature `grades`):** nueva pantalla `/grades` que, según el rol, muestra la vista del Estudiante (detalle + promedio) o del Profesor (matriz + promedio), construida sobre el design system. Ruta protegida por rol (Estudiante y Profesor) e ítem de sidebar visible para ambos.
- **Sin notificaciones por correo:** la consulta es de solo lectura y no genera envíos.

## Capabilities

### New Capabilities

- `grade-consultation-management`: consulta de calificaciones por Estudiante y Profesor. Incluye el endpoint role-aware `GET /api/courses/<id>/grades`, la vista del Estudiante (detalle por tarea + promedio propio), la vista del Profesor (matriz estudiante × tarea de los inscriptos + promedio del curso), la regla de promedio simple sobre tareas activas (nota si corregida; 1 si venció sin entrega) y la autorización por curso/rol. No genera notificaciones.

### Modified Capabilities

<!-- Ninguna capacidad existente cambia sus requisitos. La visibilidad del Estudiante se difirió desde CU-08 como decisión de implementación (D-032.4), no como requisito de spec; `grading-management` (corrección) y `submission-management` (entrega) describen operaciones distintas y no se modifican. Se dejan vacías a propósito. -->

## Impact

- **Backend:** nuevo `services/grade_service.py` (cálculo de promedio y armado de vistas Estudiante/Profesor), nuevo `blueprints/grades.py` (endpoint role-aware) registrado en `app.py`. Reutiliza `grading_service.serialize_submission` como referencia de campos, `course_service.get_manageable_course` (Profesor), `course_service.get_course_or_404`, `task_service.as_utc`/`now_utc` y `now_utc` para la regla de plazo. No se modifica el modelo ni el esquema: **no hay migración** (se leen `Task`, `Submission`, `Enrollment`).
- **Frontend:** nueva feature `src/features/grades/` (`api.js`, `GradesPage.jsx` y componentes de vista por rol) siguiendo el patrón de `grading/` y `submissions/`; nueva ruta `/grades` en `App.jsx` protegida por rol (`student` y `teacher`) y nuevo ítem de sidebar para ambos roles. Reutiliza `Card`, `DataTable`, `Badge`/`StatusBadge`, `PageHeader`, `EmptyState`, `Spinner` del design system.
- **API:** un nuevo endpoint de solo lectura `GET /api/courses/<id>/grades`. No cambia ningún endpoint existente. Se agrega al inventario de la API en `AGENTS.md`.
- **Datos / esquema:** sin cambios de esquema; no se genera migración.
- **Fuera de alcance:** chatbot LangChain + Ollama, adjuntos de archivos, notificaciones por correo, CU-10 (filtrado de usuarios). La corrección (CU-08) y la entrega (CU-07) no cambian.
