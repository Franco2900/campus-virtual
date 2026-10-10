# Proposal

## Why

CU-03 exige que el Administrador cree, consulte, modifique y desactive cursos, pero el sistema no tiene ninguna entidad de curso ni forma de acceder como Administrador. Sin la gestión de cursos, los CU-05 a CU-09 (inscripciones, tareas, entregas, calificaciones) no tienen sobre qué operar. Además, hoy no existe ningún camino reproducible para provisionar la primera cuenta de Administrador (CU-01 fuerza el rol Estudiante y la asignación de roles recién llega en CU-04), lo que bloquea tanto el uso como la verificación del CU.

## What Changes

- Introducir la entidad `Course` (nombre, código, descripción, estado activo/inactivo, fecha de creación).
- Endpoints de gestión de cursos, restringidos al rol Administrador:
  - `GET /api/courses` — listar cursos (incluye inactivos por defecto).
  - `POST /api/courses` — crear curso.
  - `GET /api/courses/<id>` — consultar un curso.
  - `PUT /api/courses/<id>` — modificar un curso.
  - `PATCH /api/courses/<id>` — activar/desactivar (baja lógica, sin borrado físico).
- Validaciones en `services/`: `name` y `code` obligatorios; `code` único (comparación case-insensitive); `name` no único; longitud acotada de `code`/`name`/`description`.
- Baja lógica y reactivación: un curso inactivo no se trata como activo y puede volver a activarse.
- Bootstrap del Administrador inicial: script `scripts/seed_admin.py` que crea la cuenta Administrador y datos de demo a partir de variables de entorno obligatorias (`CAMPUS_ADMIN_EMAIL`, `CAMPUS_ADMIN_PASSWORD`), de forma idempotente (si el admin ya existe, no falla ni duplica).
- Reutilizar el control de acceso existente (`@login_required` + `@require_roles(UserRole.ADMIN)`) para todas las rutas del CU.
- Frontend: introducir ruteo con `react-router-dom` y pantalla de administración de cursos (listado, alta, edición, activar/desactivar) con guard por rol.
- **Fuera de alcance:** asignación de profesores al curso (se define en CU-04); inscripción de estudiantes (CU-05); borrado físico de cursos.

## Capabilities

### New Capabilities

- `course-management`: gestión de cursos por el Administrador (alta, consulta, modificación, activación/desactivación) y provisión del Administrador inicial para poder operar el CU.

### Modified Capabilities

Ninguna.

## Impact

- **Backend:** nuevo `backend/models/course.py`, `backend/services/course_service.py`, `backend/blueprints/courses.py`; registro del blueprint en `backend/app.py` (tabla nueva cubierta por `db.create_all()`, sin migración). Reutiliza `backend/blueprints/guards.py`.
- **Scripts:** nuevo `scripts/seed_admin.py` (stdlib + modelo existente), invocable de forma portable.
- **Dependencias:** nueva dependencia de frontend `react-router-dom` (ruteo). Backend sin dependencias nuevas.
- **Tests:** nuevo `backend/tests/test_courses.py` (servicio + endpoints: 401 sin sesión, 403 por rol, 400 validación, 409 duplicado, baja lógica/reactivación) y test del seed admin (login + acceso por rol).
- **Frontend:** nueva dependencia de ruteo, `src/features/courses/api.js`, pantalla de cursos por rol, reorganización de `src/App.jsx` sobre el router.
- **Docs:** tabla de API en `AGENTS.md`, `decisiones.md` (bootstrap del admin, ruteo), `casos_de_uso.md` (si aporta), `progreso.md`, `tiempos.md`, `prompts_log.md`, README.
