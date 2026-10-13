# Tasks

## 1. Persistencia y alcance del Estudiante

- [ ] 1.1 Crear `backend/models/submission.py` (`Submission`: `task_id`, `student_id`, `content`, `links`, `created_at`, `updated_at`, `UNIQUE(task_id, student_id)`) y registrarlo en `app.py`; verificar `python -m pytest tests/test_migrations.py`
- [ ] 1.2 Generar la migración Alembic `0006_add_submission` y aplicarla con `flask --app app db upgrade`, verificando el head con `flask db current`
- [ ] 1.3 Extender `course_service.list_courses_for_user` y `GET /api/courses/mine` al rol Estudiante (cursos con inscripción activa) y cubrirlo en `tests/test_courses.py`/`tests/test_enrollments.py`

## 2. Backend: servicio y listado de entregas

- [ ] 2.1 Implementar `backend/services/submission_service.py` (guard de inscripción activa, disponibilidad/plazo en UTC, validación de `content`/`links`, crear/actualizar/eliminar) con el orden de validaciones D-I y verificar con `ruff check backend`
- [ ] 2.2 Ajustar `task_service.list_tasks` y `blueprints/tasks.py` para el listado role-aware (Profesor: todas; Estudiante: disponibles + entrega propia) y verificar sin regresión `python -m pytest tests/test_tasks.py`

## 3. Backend: endpoints de entrega y tests

- [ ] 3.1 Implementar `backend/blueprints/submissions.py` (`POST/PUT/DELETE /api/courses/<id>/tasks/<task_id>/submission`) con `@login_required` + `@require_roles(UserRole.STUDENT)` y registrar el blueprint en `app.py`
- [ ] 3.2 Escribir `backend/tests/test_submissions.py` (401/403 rol/403 no inscripto/404 curso y tarea, 201 y 400 de validación, 409 duplicado, 409 tarea inactiva y plazo vencido, PUT y DELETE con sus 404/409, normalización UTC) y verificar con `python -m pytest tests/test_submissions.py`

## 4. Frontend: entrega del Estudiante

- [ ] 4.1 Crear `frontend/src/features/submissions/api.js` y `SubmissionForm.jsx` (texto + links) sobre el design system y verificar `cmd /c npm run lint:format`
- [ ] 4.2 Crear `SubmissionsPage.jsx` (selector de curso vía `GET /api/courses/mine`, listado de tareas disponibles con estado de entrega, alta/edición y eliminación con confirmación) y verificar `cmd /c npm run build`
- [ ] 4.3 Registrar la ruta `/submissions` (rol `student`) en `App.jsx` e ítem en `Sidebar.jsx`, y verificar `cmd /c npm run build`

## 5. Verificación end-to-end y evidencia

- [ ] 5.1 Escribir `scripts/smoke_cu07.py` y correr `scripts/verify.py --cu cu07` (base temporal aislada) verificando el smoke verde
- [ ] 5.2 Capturar evidencia UI con Playwright (claro/oscuro) en `evidencias/cu-07/` verificando el flujo completo y consola sin errores inesperados

## 6. Revisión, documentación y cierre

- [ ] 6.1 Ejecutar la revisión del CU (subagente `reviewer` o skill `review-use-case` inline) y persistir `reviews/cu-07.md` con veredicto y mapa de evidencia
- [ ] 6.2 Actualizar `progreso.md`, tabla de API de `AGENTS.md`, `decisiones.md` (D-031+) y `README.md` si corresponde
- [ ] 6.3 Archivar el cambio openspec y validar con `openspec validate --specs --strict`
