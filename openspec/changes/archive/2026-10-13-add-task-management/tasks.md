# Tasks

## 1. Persistencia y alcance por curso

- [x] 1.1 Crear `backend/models/task.py` con `Task` (`course_id`, `title`, `description`, `due_date`, `active`, `created_at`) y verificar que `python -m pytest tests/test_migrations.py` sigue pasando
- [x] 1.2 Mover `get_manageable_course` de `enrollment_service.py` a `course_service.py` (mismo comportamiento) y verificar que `python -m pytest tests/test_enrollments.py` pasa sin cambios
- [x] 1.3 Generar la migración Alembic `0005_add_task` y aplicarla con `flask --app app db upgrade`, verificando el head con `flask db current`

## 2. Backend: servicio y endpoints de tareas

- [x] 2.1 Implementar `backend/services/task_service.py` (`list_tasks`, `get_task`, `create_task`, `update_task`, `set_task_active`) con el orden de validaciones D-J y verificar con `ruff check backend`
- [x] 2.2 Implementar `backend/blueprints/tasks.py` (`GET/POST /api/courses/<id>/tasks`, `GET/PUT/PATCH /api/courses/<id>/tasks/<task_id>`) con `@login_required` + `@require_roles(UserRole.TEACHER)` y registrar el blueprint en `app.py`
- [x] 2.3 Escribir `backend/tests/test_tasks.py` (401/403 rol/403 Profesor ajeno/404 curso y tarea, creación 201, validaciones 400, curso inactivo 409, modificación de fecha límite, PATCH `active`) y verificar con `python -m pytest tests/test_tasks.py`

## 3. Frontend: gestión de tareas

- [x] 3.1 Crear `frontend/src/features/tasks/api.js` y `TaskForm.jsx` sobre el design system y verificar `cmd /c npm run lint:format`
- [x] 3.2 Crear `TasksPage.jsx` (selector de curso vía `GET /api/courses/mine`, tabla, alta/edición, activar/desactivar) y verificar `cmd /c npm run build`
- [x] 3.3 Registrar la ruta `/tasks` (rol `teacher`) en `App.jsx` e ítem en `Sidebar.jsx`, y verificar `cmd /c npm run build`

## 4. Verificación end-to-end y evidencia

- [x] 4.1 Escribir `scripts/smoke_cu06.py` y correr `scripts/verify.py --cu cu06` (base temporal aislada) verificando el smoke verde
- [x] 4.2 Capturar evidencia UI con Playwright (claro/oscuro) en `evidencias/cu-06/` verificando el flujo completo y consola sin errores inesperados

## 5. Revisión, documentación y cierre

- [x] 5.1 Ejecutar la revisión del CU (subagente `reviewer` o skill `review-use-case` inline) y persistir `reviews/cu-06.md` con veredicto y mapa de evidencia
- [x] 5.2 Actualizar `progreso.md`, tabla de API de `AGENTS.md`, `decisiones.md` (D-026+), `prompts_log.md`, `README.md` y `tiempos.md`
- [x] 5.3 Archivar el cambio openspec y validar con `openspec validate --specs --strict`
