# Tasks

## 1. Esquema — modelo `Enrollment` y migración `0004`

- [x] 1.1 Crear `backend/models/enrollment.py` (`id`, `course_id` FK→`course.id`, `student_id` FK→`user.id`, `active` default `True`, `enrolled_at` UTC, `UNIQUE(course_id, student_id)`) y registrarlo en `backend/app.py`; verificar `pytest` (suite existente + test de paridad modelos↔migraciones)
- [x] 1.2 Generar la migración `0004` con `flask db migrate -m "add enrollment"` y aplicarla con `flask db upgrade` sobre la base real y la temporal de `scripts/verify.py`; verificar `test_migrations.py` sin drift y `flask db current`

## 2. Backend — servicio y endpoints de inscripciones

- [x] 2.1 Agregar `ForbiddenError` a `backend/services/errors.py` y crear `backend/services/enrollment_service.py` (`get_manageable_course`, `list_students`, `enroll_student`, `set_enrollment_active`, `remove_enrollment`) con el orden de validaciones de D-D y validaciones solo en `services/`; verificar con tests de servicio
- [x] 2.2 Crear `backend/blueprints/enrollments.py` (`GET/POST /api/courses/<id>/students`, `PATCH/DELETE /api/courses/<id>/students/<student_id>`) con `@login_required` + `@require_roles(UserRole.ADMIN, UserRole.TEACHER)` y mapeo de `ForbiddenError`→403; registrarlo en `app.py`; verificar con tests: 401/403 (rol y Profesor no asignado), 200 listado con/sin inscripción, 201 alta, 409 duplicado/curso inactivo, 400 cuenta no estudiante/inactiva y `active` inválido, 200 activar/desactivar y eliminar, 404 curso/estudiante/inscripción
- [x] 2.3 Agregar `GET /api/courses/mine` en `backend/blueprints/courses.py` (Profesor: asignados vía `course_teacher`; Admin: todos) y actualizar `AGENTS.md` (tabla de API) y `decisiones.md` con las decisiones del CU-05; verificar con tests: Profesor con y sin cursos, Admin todos, 401/403
- [x] 2.4 Ejecutar la suite completa (`..\.venv\Scripts\python.exe -m pytest -q` desde `backend/`) y `ruff check` + `ruff format --check`; verificar que pasan los tests previos + `test_enrollments.py`

## 3. Frontend — pantalla de inscripciones

- [x] 3.1 Crear `frontend/src/features/enrollments/api.js` (listMyCourses, listStudents, enrollStudent, setEnrollmentActive, removeEnrollment) sobre `src/api/client.js`; verificar que `cmd /c npm run build` compila
- [x] 3.2 Crear `EnrollmentsPage.jsx` sobre el design system (DataTable, Badge de estado, Button, ConfirmDialog, EmptyState, Toast, FormField) con selector de curso, acciones inscribir/activar/desactivar/eliminar, errores del backend renderizados y deshabilitado en cursos inactivos; `data-testid` por elemento; verificar build + `npm run lint:format`
- [x] 3.3 Extender `ProtectedRoute` con `roles` (array, compatible con `role`), agregar la ruta `/enrollments` (Admin/Profesor) en `src/App.jsx` y el ítem "Inscripciones" en `Sidebar.jsx` (Admin/Profesor); actualizar `README.md`; verificar build y que un Estudiante no ve la vista

## 4. Verificación integrada y evidencia

- [x] 4.1 Crear `scripts/smoke_cu05.py` (Admin: crear curso/estudiante, inscribir, duplicado 409, desactivar/reactivar, eliminar, curso inactivo 409; Profesor: `/mine` solo asignados, inscribir en su curso, 403 en curso ajeno) y correr `scripts/verify.py --cu cu05`; verificar salida sin fallos y cleanup
- [x] 4.2 Capturar evidencia de UI con Playwright en `evidencias/cu-05/` (`NN-accion.png`) en claro y oscuro: listado de estudiantes con estados, inscripción, desactivación, eliminación, curso ajeno bloqueado (Profesor) y listado vacío (Profesor sin cursos); verificar consola sin errores inesperados

## 5. Cierre — documentación, revisión, archivo y commits

- [x] 5.1 Actualizar `progreso.md` (CU-05 Completada, corregir el texto stale del OK docente), `prompts_log.md` y `tiempos.md`; verificar que reflejan el estado real
- [x] 5.2 Revisar con el subagente `reviewer` (o skill `review-use-case` inline si falla por tier) y corregir bloqueantes hasta APROBADO; persistir `reviews/cu-05.md` con hallazgos, severidad, veredicto y mapa de evidencia
- [x] 5.3 Archivar el cambio (`openspec archive add-enrollment-management --yes`) y verificar `openspec validate --specs --strict` sin errores; commitear por unidad de trabajo (conventional commits) y verificar `git status` limpio