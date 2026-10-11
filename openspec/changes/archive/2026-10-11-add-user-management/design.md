# Design

## Context

CU-02 dejó autenticación por cookie firmada y el guard de rol `require_roles` (`backend/blueprints/guards.py`). CU-03 introdujo el patrón de dominio gestionado por rol (`course`), la separación `routes → services → models` con validaciones en `services/` y el patrón de errores (`services/errors.py` → 400/409/404). CU-04 es el primer caso que (a) modifica el esquema de una tabla existente con datos (`user`) y (b) crea una relación N:M (`profesor↔curso`). Por eso es el punto correcto para introducir migraciones formales. Ver `proposal.md - Why` y `specs/user-management/spec.md`.

## Goals / Non-Goals

**Goals:**
- Gestión de usuarios por el Administrador: listar (incluye inactivos), consultar, editar identidad y rol, activar/desactivar (baja lógica) y resetear contraseña.
- Respetar la regla de exactamente un rol por usuario (los roles son mutuamente excluyentes).
- Bloquear la autogestión peligrosa: un Admin no puede desactivarse ni quitarse el rol Admin a sí mismo.
- Relación profesor↔curso (asignar/quitar/listar), exclusiva del Administrador; solo se asignan cuentas con rol Profesor.
- Adoptar migraciones (Flask-Migrate/Alembic) preservando los datos existentes del esquema pre-CU-04.
- Frontend sobre el design system, con guard por rol y evidencia por estado.

**Non-Goals:**
- Filtrado/búsqueda de usuarios (CU-10).
- Inscripción de estudiantes a cursos (CU-05).
- Borrado físico de usuarios o cursos.
- Alta de usuarios por el Administrador (el registro público de CU-01 sigue siendo la vía).
- Expiración o forzado de cambio de la contraseña reseteada.
- Autenticación de dos factores o revocación inmediata de sesiones activas.

## Decisions

- **D-A — Estado activo en `User`.** Se agrega `active` (Boolean, NOT NULL, default `True`) a `user`. La desactivación es lógica (sin borrado físico). Alternativa descartada: borrado físico (rompe integridad referencial con cursos/tareas futuras y no es reversible).
- **D-B — Campos editables por el Admin.** `PUT /api/users/<id>` permite cambiar `first_name`, `last_name`, `email` y `role`; `PATCH /api/users/<id>` con body `{"active": <bool>}` cambia el estado; `POST /api/users/<id>/password` con body `{"password": <str>}` resetea la contraseña (decisión del usuario). La contraseña se hashea con `generate_password_hash` (mismo mecanismo que CU-01). Alternativa descartada: contraseña temporal generada por el sistema (suma flujo de expiración/forzado de cambio, fuera del alcance del CU).
- **D-C — Autorización y guard de autogestión.** Todos los endpoints de usuarios y de profesores usan `@login_required` + `@require_roles(UserRole.ADMIN)`. Regla adicional: si el objetivo es la propia cuenta del Admin autenticado y la operación es desactivarla o cambiar su rol a otro distinto de Administrador, el `service` lanza `ValidationError` → HTTP 400 con mensaje claro. Esto evita que un Admin se deje sin acceso o deje al sistema sin ningún Administrador activo. Alternativa considerada: HTTP 403 (semánticamente "prohibido"); se optó por 400 por consistencia con el resto de reglas de negocio validadas en `services/` (403 queda reservado al guard de rol).
- **D-D — Endpoints y semántica.** `GET /api/users` (lista completa, incluye inactivos), `GET /api/users/<id>` (200/404), `PUT /api/users/<id>` (200/400/404/409), `PATCH /api/users/<id>` (200/400/404), `POST /api/users/<id>/password` (200/400/404). La serialización expone `id`, `first_name`, `last_name`, `email`, `role`, `active`, `created_at` y MUST NOT exponer `password_hash`. El email se normaliza a minúsculas y es único case-insensitive (misma regla que el registro), excluyendo la propia cuenta en la edición (409 ante colisión).
- **D-E — Relación profesor↔curso.** Nueva tabla `course_teacher` con `id` (PK), `course_id` (FK→`course.id`, NOT NULL), `teacher_id` (FK→`user.id`, NOT NULL) y `UNIQUE(course_id, teacher_id)`. Se expone como subrecurso de curso: `GET /api/courses/<id>/teachers`, `POST /api/courses/<id>/teachers` (body `{"teacher_id": <int>}`) y `DELETE /api/courses/<id>/teachers/<teacher_id>`, todos solo Administrador. Validaciones en `services/`: curso existente (404), usuario existente (404), usuario con rol Profesor (400), duplicado (409). Alternativa considerada: endpoint sobre el usuario (`/api/users/<id>/courses`); se optó por el subrecurso de curso por coherencia con la UI (asignar profesores al editar un curso) y con el caso de uso "gestión por curso".
- **D-F — Migraciones con Flask-Migrate.** Se agrega `Flask-Migrate` (que integra Alembic) y `backend/migrations/`. Estrategia: (1) baseline `0001` que refleja el esquema pre-CU-04 (`user` sin `active` + `course`); (2) `flask db stamp` de la base existente en `0001` para no recrear tablas; (3) migraciones incrementales `0002` (`ALTER user ADD active`, con `server_default` para backfill de filas existentes) y `0003` (`CREATE TABLE course_teacher`), aplicadas con `flask db upgrade`. `create_app()` deja de llamar `db.create_all()` salvo cuando `TESTING` es verdadero (los tests construyen el esquema desde los modelos en base temporal, rápido y aislado). `scripts/verify.py` aplica `flask db upgrade` sobre la base temporal antes del seed. Alternativas descartadas: Alembic puro (más wiring manual sin ventaja para Flask) y recrear la base demo (pierde datos; el usuario eligió migración real).
- **D-G — Tests.** `backend/tests/test_users.py` (401/403, listado con inactivos, detalle, edición válida, email duplicado 409, rol inválido 400, faltantes 400, patch activo, autogestión bloqueada 400, reset de contraseña ok/corta 400, serialización sin `password_hash`) y `backend/tests/test_course_teachers.py` (asignar profesor 201/200, no-teacher 400, duplicado 409, curso/usuario inexistente 404, quitar 200, listar, 403 no-admin). Test de paridad: `flask db upgrade` sobre base temporal produce un esquema con las mismas tablas/columnas que los modelos.

## Risks / Trade-offs

- [Migración sobre datos existentes] → El baseline + stamp evita recrear tablas; el delta solo agrega una columna con default y una tabla nueva. Rollback: `flask db downgrade` a `0001` (elimina `course_teacher` y la columna `active`); documentado.
- [Mezclar `create_all` (tests) y migraciones (dev)] → Se limita `create_all()` a `TESTING`; el test de paridad detecta drift entre modelos y migraciones.
- [Reset de contraseña por el Admin] → El Admin fija la contraseña; no hay expiración ni forzado de cambio. La contraseña MUST NOT registrarse en logs ni devolverse en respuestas.
- [Guard de autogestión] → Cubre desactivación y cambio de rol, pero no impide que un Admin borre el rol de *otro* Admin dejando un solo Admin; aceptable para el TP y consistente con la regla de negocio (cada usuario conserva exactamente un rol).
- [Universo de profesores para asignar] → El frontend lista cuentas con rol Profesor; si no hay ninguno, la asignación no tiene candidatos hasta que CU-04 mismo promueva una cuenta (flujo cubierto por el smoke).
- [Filtrado fuera de alcance] → CU-10 cubrirá búsqueda/filtros; el listado de CU-04 no los incluye.

## Migration Plan

1. `flask db init` (crea `backend/migrations/`).
2. `flask db migrate -m "baseline pre CU-04"` contra una base temporal vacía → `0001` (esquema pre-CU-04).
3. `flask db stamp 0001` sobre `backend/instance/campus.db` (marca el estado actual sin recrear tablas).
4. Implementar el cambio de modelo de usuario y `flask db migrate -m "add user active"` → `0002`; implementar `course_teacher` y `flask db migrate -m "add course teacher"` → `0003`.
5. `flask db upgrade` sobre la base real aplica `0002` y `0003`.
6. Entornos nuevos: `flask db upgrade` construye todo desde cero.

Rollback: `flask db downgrade 0001` revierte `0003` y `0002`. Sin migraciones productivas que preservar fuera del TP.

## Open Questions

Ninguna que afecte specs, enfoque o tareas.
