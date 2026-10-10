# Tasks

## 1. Backend — modelo `Course` y bootstrap del Administrador

- [x] 1.1 Crear `backend/models/course.py` (`Course`: `id`, `name`, `code` único, `description`, `active` default `True`, `created_at` UTC) y registrarlo en el factory (`backend/app.py`); verificar que al crear la app se crea la tabla (test que inserta y consulta un `Course`)
- [x] 1.2 Crear `scripts/seed_admin.py` portable: lee `CAMPUS_ADMIN_EMAIL`/`CAMPUS_ADMIN_PASSWORD` (obligatorias), crea el admin con `role=ADMIN` y 4 cursos de demo (activos e inactivos), idempotente (skip si el admin ya existe); verificar con tests: provisión exitosa (login del admin OK), env faltante (falla sin crear cuentas) y segunda ejecución (no duplica, sin error)
- [x] 1.3 Ejecutar la suite (`..\.venv\Scripts\python.exe -m pytest -q` desde `backend/`) y verificar que los tests nuevos del modelo y del seed pasan

## 2. Backend — servicio y endpoints de gestión de cursos

- [x] 2.1 Crear `backend/services/course_service.py` (list/get/create/update/set_active) con validaciones en la capa service: nombre y código obligatorios y no vacíos, longitudes acotadas, `code` normalizado a mayúsculas y único case-insensitive, `description` opcional; lanzar `ValidationError`/`ConflictError`/`NotFoundError`; verificar con tests de servicio (alta, duplicado case-insensitive, faltantes, inexistente)
- [x] 2.2 Crear `backend/blueprints/courses.py` con los endpoints `GET/POST /api/courses`, `GET/PUT/PATCH /api/courses/<id>` protegidos por `@login_required` + `@require_roles(UserRole.ADMIN)` y registrar el blueprint en `app.py`; verificar con tests: 401 sin sesión, 403 con Estudiante/Profesor, 201 alta, 400 faltantes, 409 duplicado, 200 listado (incluye inactivos), 404 en get/put/patch inexistente, patch desactiva y reactiva
- [x] 2.3 Ejecutar la suite completa (`..\.venv\Scripts\python.exe -m pytest -q` desde `backend/`) y verificar que pasan los tests previos + `test_courses.py`

## 3. Frontend — ruteo y pantalla de cursos por rol

- [x] 3.1 Agregar `react-router-dom` a `frontend/package.json` e instalarlo; verificar que `cmd /c npm run build` (desde `frontend/`) compila
- [x] 3.2 Agregar `frontend/src/features/courses/api.js` (list/create/get/update/setActive sobre `src/api/client.js`); verificar que el build compila
- [x] 3.3 Reorganizar `frontend/src/App.jsx` con `BrowserRouter` (rutas `/login`, `/register`, `/courses`) restaurando la sesión con `getMe()` y protegiendo `/courses` por rol Administrador; verificar que el build compila y que un rol no admin no ve la vista de cursos
- [x] 3.4 Crear la pantalla de cursos (listado con estado activo/inactivo, alta, edición, activar/desactivar, errores del backend renderizados); verificar que el build compila

## 4. Verificación integrada y documentación

- [x] 4.1 Smoke end-to-end con `scripts/verify.py --cu CU-03`: seed del admin, login, alta de curso (201) + duplicado (409) vía proxy; verificar salida sin fallos y cleanup de procesos
- [x] 4.2 Capturar evidencia de UI con Playwright en `evidencias/cu-03/` (`NN-accion.png`): login admin, listado de cursos, alta, desactivar/reactivar, error renderizado; verificar consola sin errores inesperados
- [x] 4.3 Actualizar `AGENTS.md` (tabla API con los endpoints de cursos y auth/rol), `decisiones.md` (D-017 bootstrap del admin, D-018 ruteo), `README.md`, `progreso.md` (CU-03) y `prompts_log.md`; verificar que cada documento refleja el estado real

## 5. Revisión, archivo y commits

- [x] 5.1 Revisar con el subagente `reviewer` (o skill `review-use-case` inline si falla por tier) y corregir bloqueantes hasta APROBADO; persistir `reviews/cu-03.md` con hallazgos, severidad, veredicto y mapa de evidencia
- [x] 5.2 Archivar el cambio openspec (`openspec archive add-course-management --yes`) y verificar `openspec validate --specs --strict` sin errores
- [ ] 5.3 Registrar tiempos en `tiempos.md`, cerrar `track-time` y commitear por unidad de trabajo (conventional commits); verificar `git status` limpio y `git log` coherente
