# Proposal

## Why

CU-04 exige que el Administrador gestione las cuentas de usuarios y sus roles, pero hoy el sistema no tiene ninguna entidad de gestión sobre usuarios: no se puede listar, editar, cambiar de rol ni desactivar una cuenta. Además, la asignación del rol Profesor es competencia exclusiva del Administrador (regla de negocio de roles mutuamente excluyentes) y la relación profesor↔curso quedó explícitamente diferida a este CU por CU-03 (D-017). Sin esta gestión, CU-05 (inscripciones) no puede resolver "un profesor solo opera sobre los cursos en los que trabaja" ni el sistema puede provisionar profesores. Este cambio también introduce el primer cambio de esquema con datos existentes, por lo que adopta migraciones formales (Alembic vía Flask-Migrate).

## What Changes

- Extender la entidad `User` con el estado activo/inactivo (baja lógica).
- Introducir la relación profesor↔curso mediante una tabla de asociación `course_teacher`.
- Endpoints de gestión de usuarios, restringidos al rol Administrador:
  - `GET /api/users` — listar usuarios (incluye inactivos).
  - `GET /api/users/<id>` — consultar una cuenta.
  - `PUT /api/users/<id>` — modificar datos de identidad y rol.
  - `PATCH /api/users/<id>` — activar/desactivar (baja lógica, sin borrado físico).
  - `POST /api/users/<id>/password` — resetear la contraseña.
- Endpoints de asignación de profesores a un curso, restringidos al rol Administrador:
  - `GET /api/courses/<id>/teachers` — listar los profesores asignados.
  - `POST /api/courses/<id>/teachers` — asignar un profesor al curso.
  - `DELETE /api/courses/<id>/teachers/<teacher_id>` — quitar un profesor del curso.
- Validaciones en `services/`: email obligatorio, con formato válido y único case-insensitive (excluyendo la propia cuenta); rol MUST ser un rol válido; nombres obligatorios; contraseña MUST tener longitud mínima; el rol Profesor asignado a un curso MUST corresponder a una cuenta con ese rol.
- Guard de autogestión: un Administrador MUST NOT poder desactivarse ni quitarse el rol Administrador a sí mismo.
- Adopción de migraciones con Flask-Migrate: baseline del esquema pre-CU-04, stamp de la base existente y migración incremental de este cambio.
- Frontend: pantalla de administración de usuarios (listado, edición de datos y rol, activar/desactivar, reset de contraseña) y gestión de profesores por curso, sobre el design system existente, con guard por rol.
- **Fuera de alcance:** filtrado/búsqueda de usuarios (CU-10); inscripción de estudiantes (CU-05); borrado físico de usuarios o cursos; expiración/forzado de cambio de la contraseña reseteada; alta de usuarios por el Administrador (CU-01 mantiene el registro público).

## Capabilities

### New Capabilities

- `user-management`: gestión de usuarios por el Administrador (listado, consulta, edición de datos y rol, activación/desactivación lógica y reseteo de contraseña) bajo la regla de exactamente un rol por usuario.

### Modified Capabilities

- `course-management`: se agrega la asignación y remoción de profesores por curso (relación profesor↔curso), operación exclusiva del Administrador.

## Impact

- **Backend:** `backend/models/user.py` (columna `active`), nuevo `backend/models/course_teacher.py`, nuevo `backend/blueprints/users.py`, `backend/services/user_service.py` (list/get/update/set_active/reset_password), nuevo `backend/services/course_teacher_service.py` (assign/remove/list), extensión de `backend/blueprints/courses.py` con los endpoints de profesores, y registro en `backend/app.py`. La tabla nueva y la columna se aplican con una migración incremental.
- **Migraciones:** nueva dependencia `Flask-Migrate` (Alembic); se crea `backend/migrations/` con el baseline del esquema pre-CU-04 y la migración incremental de este cambio. `create_app()` deja de crear el esquema salvo en modo `TESTING`; los entornos de desarrollo y verificación aplican `flask db upgrade`.
- **Scripts:** `scripts/verify.py` migra la base temporal antes de sembrar; nuevo `scripts/smoke_cu04.py`.
- **Tests:** nuevo `backend/tests/test_users.py` (servicio + endpoints + autogestión + reset) y `backend/tests/test_course_teachers.py` (asignación/remoción); test de paridad migraciones↔modelos. Los tests usan `db.create_all()` sobre base temporal (modo `TESTING`).
- **Frontend:** `src/features/users/` (api + pantalla), gestión de profesores dentro de `src/features/courses/`, ruta `/users` (guard Administrador) e ítem de navegación en el shell.
- **Docs:** `AGENTS.md` (tabla de API, flujo de migraciones, roadmap), `decisiones.md` (gestión de usuarios, relación profesor↔curso, adopción de Flask-Migrate y ajuste de D-010), `README.md`, `progreso.md`, `tiempos.md`, `prompts_log.md`.
