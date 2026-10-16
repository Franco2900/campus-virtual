# Proposal

## Why

CU-04 (Gestionar usuarios) dejó al Administrador con `GET /api/users` que devuelve **todos** los usuarios ordenados por id, sin ninguna forma de acotar la lista. Con el crecimiento del plantel (estudiantes, profesores y admins mezclados, activos e inactivos), encontrar una cuenta concreta obliga a escanear la tabla completa. CU-10 («Filtrar usuarios», `casos_de_uso.md`) es el último caso de uso pendiente del alcance y define que el Administrador debe poder buscar y filtrar usuarios; CU-04 y CU-05 difirieron explícitamente el filtrado a CU-10 (`2026-10-11-add-user-management`, `2026-10-11-add-enrollment-management`).

## What Changes

- **Filtrado server-side en `GET /api/users`:** el endpoint acepta query params opcionales `q` (texto libre sobre nombre, apellido y correo), `role` (rol exacto) y `active` (estado), combinados con AND. Sin criterios (o con todos vacíos) la respuesta es idéntica a la actual: todos los usuarios ordenados por id. La forma del arreglo de usuarios serializados **no cambia**.
- **Validación de criterios en `services/`:** `role` debe ser un valor válido del enum `UserRole` y `active` uno de los strings `true`/`false`; valores inválidos responden HTTP 400 con mensaje claro en español. `q` se limpia (trim); vacío = sin criterio.
- **Frontend (feature `users`):** barra de filtros sobre el `Card` de la tabla de `UsersPage` (texto, rol, estado) construida con el design system, con recarga server-side al cambiar los selects y debounce (~300 ms) para el texto, más botón «Limpiar filtros».
- **Estado vacío diferenciado (flujo A1):** «sin resultados para los criterios» se distingue visualmente de «Todavía no hay usuarios registrados», con icono y CTA para limpiar los filtros.
- **Sin cambios de datos:** el filtro es de solo lectura; no modifica usuarios, no borra nada y no genera notificaciones.

## Capabilities

### New Capabilities

- `user-filtering`: filtrado de usuarios por el Administrador mediante query params en `GET /api/users` (texto libre `q`, rol `role`, estado `active`, combinados con AND), con validación de criterios, preservación de la forma de respuesta, distinción del estado vacío A1 y la garantía de solo lectura.

### Modified Capabilities

<!-- `user-management` no cambia: su requisito de listado ("listar todas las cuentas... activas como inactivas") sigue vigente como comportamiento SIN criterios, que este cambio preserva byte a byte. El filtrado es aditivo y se documenta como capacidad nueva. Se deja vacío a propósito. -->

## Impact

- **Backend:** `backend/services/user_service.py` — `list_users()` acepta criterios opcionales y arma el query con `ilike` sobre `first_name`/`last_name`/`email` y filtros de igualdad sobre `role`/`active`; nuevas validaciones de `role`/`active` con `ValidationError` (400). `backend/blueprints/users.py` — `list_users_endpoint` lee los query params y se los pasa al servicio (la autorización `@login_required` + `require_roles(ADMIN)` no cambia). **No cambian modelos ni esquema: sin migración.**
- **Tests backend:** extensión de `backend/tests/test_users.py` (o archivo dedicado de filtrado) con los criterios individuales, combinados, inválidos y de autorización.
- **Frontend:** `frontend/src/features/users/api.js` (`listUsers` acepta criterios) y `frontend/src/features/users/UsersPage.jsx` (barra de filtros, debounce, limpiar y empty state A1) sobre `src/ui/` (`FormField`, `EmptyState`, `Button`, `DataTable`). Reutiliza como referencia de estilo el buscador de estudiantes de CU-05 (`features/enrollments/EnrollmentsPage.jsx`).
- **Scripts:** `scripts/smoke_cu10.py` (patrón `smoke_cu09.py`) conectado a `scripts/verify.py`.
- **API:** no se agrega ni elimina endpoints; `GET /api/users` incorpora query params documentados en la tabla de `AGENTS.md`.
- **Documentación:** tabla de API en `AGENTS.md`, `progreso.md` (CU-10 Completo), `decisiones.md` si corresponde, evidencia en `evidencias/cu-10/` y revisión en `reviews/cu-10.md`.
- **Fuera de alcance:** paginación (el universo es chico), borrado de usuarios, pantalla nueva de detalle (el modal de edición de CU-04 cubre el paso 6 del flujo), filtrado de otras entidades (cursos, tareas, inscripciones), chatbot, notificaciones por correo.
