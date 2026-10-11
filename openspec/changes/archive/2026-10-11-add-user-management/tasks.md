# Tasks

## 1. Migraciones — Flask-Migrate, baseline y stamp

- [x] 1.1 Agregar `Flask-Migrate` a `backend/requirements.txt` e instalarlo; registrar `Migrate(app, db)` en `backend/app.py` y limitar `db.create_all()` a `app.config["TESTING"]`; verificar que los tests existentes siguen pasando
- [x] 1.2 `flask db init` (`backend/migrations/`); generar el baseline `0001` del esquema pre-CU-04 contra una base temporal vacía; `flask db stamp 0001` sobre `backend/instance/campus.db`; verificar con `flask db current`/`flask db history`
- [x] 1.3 Ajustar `scripts/verify.py` para aplicar `flask db upgrade` sobre la base temporal antes del seed; verificar con `python scripts/verify.py --cu cu03` (regresión: 13/13 PASS)

## 2. Backend — estado activo y gestión de usuarios

- [x] 2.1 Agregar `active` (Boolean, NOT NULL, default `True`) a `models/user.py`; generar y aplicar la migración `0002` (`user.active`, con `server_default` para backfill de filas existentes); verificar `flask db upgrade` sobre base temporal y `pytest`
- [x] 2.2 Extender `services/user_service.py` con `list_users`, `get_user_or_404`, `update_user`, `set_user_active`, `reset_password`: validaciones en `services/` (email formato y único case-insensitive excluyendo la propia cuenta, rol válido, nombres obligatorios, contraseña con longitud mínima) y guard de autogestión; verificar con tests de servicio
- [x] 2.3 Crear `blueprints/users.py` (`GET/POST` de gestión) con `@login_required` + `@require_roles(UserRole.ADMIN)`, serialización sin `password_hash`, y registrarlo en `app.py`; verificar con tests: 401 sin sesión, 403 por rol, listado, detalle, edición, 409 email duplicado, 400 rol/faltantes, patch activo, autogestión bloqueada, reset de contraseña
- [x] 2.4 Ejecutar la suite completa (`..\.venv\Scripts\python.exe -m pytest -q` desde `backend/`) y verificar que pasan los tests previos + `test_users.py`

## 3. Backend — asignación de profesores por curso

- [x] 3.1 Crear `models/course_teacher.py` (`CourseTeacher`: `course_id` FK, `teacher_id` FK, `UNIQUE(course_id, teacher_id)`) y registrarlo en `app.py`; generar y aplicar la migración `0003`; verificar que la crea
- [x] 3.2 Crear `services/course_teacher_service.py` (`assign_teacher`, `remove_teacher`, `list_teachers`) con validaciones: curso existente, usuario existente, rol Profesor, duplicado; verificar con tests de servicio
- [x] 3.3 Extender `blueprints/courses.py` con `GET/POST /api/courses/<id>/teachers` y `DELETE /api/courses/<id>/teachers/<teacher_id>` (solo Administrador); verificar con tests: 401/403, 201/200 asignar, 400 no-teacher, 409 duplicado, 404 curso/usuario, 200 quitar y listar
- [x] 3.4 Ejecutar la suite completa y verificar que pasan `test_courses.py` + `test_course_teachers.py`

## 4. Frontend — pantalla de usuarios y profesores por curso

- [x] 4.1 Crear `frontend/src/features/users/api.js` (list/get/update/setActive/resetPassword) sobre `src/api/client.js`; verificar que `cmd /c npm run build` compila
- [x] 4.2 Crear `UsersPage.jsx` sobre el design system (DataTable, Modal, ConfirmDialog, RoleBadge, FormField, Toast) con edición de datos/rol, activar/desactivar, reset de contraseña y errores del backend renderizados; `data-testid` por elemento
- [x] 4.3 Agregar la gestión de profesores por curso en `frontend/src/features/courses/` (asignar/quitar, listar asignados); verificar que el build compila
- [x] 4.4 Agregar la ruta `/users` (guard Administrador) en `src/App.jsx` y el ítem "Usuarios" en `Sidebar.jsx`; verificar que el build compila y que un rol no admin no ve la vista

## 5. Verificación integrada y evidencia

- [x] 5.1 Crear `scripts/smoke_cu04.py` (login admin → listar usuarios → promover estudiante a Profesor → asignar a curso → listar profesores → desactivar → reset de contraseña → autogestión bloqueada 400) y correr `scripts/verify.py --cu cu04`; verificar salida sin fallos y cleanup
- [x] 5.2 Capturar evidencia de UI con Playwright en `evidencias/cu-04/` (`NN-accion.png`) en claro y oscuro: listado, edición, cambio de rol, desactivación, reset, asignación de profesor y error de autogestión; verificar consola sin errores inesperados

## 6. Documentación

- [x] 6.1 Actualizar `AGENTS.md` (tabla API de usuarios y profesores, flujo de migraciones en "Cómo ejecutar", roadmap, blueprint `users`), `decisiones.md` (gestión de usuarios, profesor↔curso, Flask-Migrate y ajuste de D-010), `README.md`, `progreso.md`, `prompts_log.md`; verificar que cada documento refleja el estado real

## 7. Revisión, archivo y commits

- [x] 7.1 Revisar con el subagente `reviewer` (o skill `review-use-case` inline si falla por tier) y corregir bloqueantes hasta APROBADO; persistir `reviews/cu-04.md` con hallazgos, severidad, veredicto y mapa de evidencia
- [x] 7.2 Archivar el cambio openspec (`openspec archive add-user-management --yes`) y verificar `openspec validate --specs --strict` sin errores
- [x] 7.3 Registrar tiempos en `tiempos.md`, cerrar `track-time` y commitear por unidad de trabajo (conventional commits); verificar `git status` limpio y `git log` coherente
