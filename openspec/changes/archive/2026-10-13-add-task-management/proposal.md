# Proposal

## Why

CU-06 exige que el Profesor cree, consulte, modifique y desactive las tareas de los cursos en los que trabaja, pero hoy el sistema no tiene ninguna entidad de tarea: no existe nada sobre lo que el Estudiante pueda entregar (CU-07) ni el Profesor corregir (CU-08), y las calificaciones (CU-09) no tienen de dónde derivarse. Sin `Task`, la cadena de evaluación del curso queda sin base.

## What Changes

- Nueva entidad de dominio `Task` (tarea), que **pertenece a un curso** y puede estar **activa o inactiva**.
- Endpoints REST para crear, listar, consultar, modificar y activar/desactivar tareas, anidados bajo el curso: `/api/courses/<id>/tasks`.
- Autorización: sólo el rol **Profesor**, y sólo sobre los cursos en los que está asociado (una tarea de un curso ajeno responde 403).
- Validaciones de tarea (título obligatorio, fecha límite válida) en la capa `services/`.
- Pantalla de gestión de tareas en el frontend (selección de curso del Profesor, listado, alta/edición y activar/desactivar).
- Sin notificaciones por correo: las modificaciones de tarea no disparan envíos (regla de `casos_de_uso.md`).

Fuera de alcance (CUs posteriores): la entrega del Estudiante (CU-07), la corrección y calificación (CU-08) y la consulta de calificaciones (CU-09).

## Capabilities

### New Capabilities
- `task-management`: creación, consulta, modificación y baja lógica de tareas por parte del Profesor, acotadas a sus cursos.

### Modified Capabilities
<!-- Sin cambios a nivel de requisitos en capacidades existentes. -->

## Impact

- **Backend:** nuevo modelo `models/task.py`, migración Alembic `0005_add_task`, `services/task_service.py`, `blueprints/tasks.py` y su registro en `app.py`. Reutiliza el guard de alcance por Profesor (`get_manageable_course`) y el patrón `ForbiddenError`/`NotFoundError`/`ValidationError`/`ConflictError` de CU-05.
- **Frontend:** nueva feature `src/features/tasks/` sobre el design system, ruta `/tasks` protegida por rol Profesor e ítem de sidebar.
- **API:** nuevos endpoints bajo `/api/courses/<id>/tasks` (documentar en `AGENTS.md`).
- **Datos:** nueva tabla `task` con `FK` a `course`; sin pérdida de datos existentes.
- **Verificación:** tests `backend/tests/test_tasks.py`, smoke `scripts/smoke_cu06.py` y evidencia UI en `evidencias/cu-06/`.
