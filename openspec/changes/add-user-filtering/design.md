# Design

## Context

Ver `proposal.md - Why`. Estado actual relevante:

- `backend/services/user_service.py::list_users()` (línea 88-89) devuelve todos los usuarios ordenados por id, sin parámetros: `db.select(User).order_by(User.id)`.
- `backend/blueprints/users.py::list_users_endpoint` (línea 29-33) expone `GET /api/users` con `@login_required` + `require_roles(UserRole.ADMIN)` y serializa `id`, `first_name`, `last_name`, `email`, `role`, `active`, `created_at`. **No** atrapa `ValidationError` (hoy el listado no valida nada).
- `models/user.py`: `UserRole` enum (`student`/`teacher`/`admin`), `User` con `first_name`, `last_name`, `email`, `role`, `active`, `created_at`. **No hay cambio de esquema** → sin migración.
- `services/errors.py` ya define `ValidationError` (mapeado a 400 en otros endpoints de users).
- `user_service.py` ya tiene `ROLE_VALUES = {role.value: role for role in UserRole}` y `_parse_role` para validar roles (reutilizables como referencia, aunque el filtrado trabaja con el string del query param).
- Frontend: `frontend/src/features/users/UsersPage.jsx` renderiza la tabla de CU-04 (`DataTable` sobre un `Card`) sin barra de filtros; `frontend/src/features/users/api.js::listUsers()` llama `get("/api/users")` sin parámetros.
- Referencia de estilo de búsqueda: `frontend/src/features/enrollments/EnrollmentsPage.jsx` (CU-05) usa `FormField` + `<input type="search">` y normaliza texto client-side (`normalizeText` con NFD) sobre una lista ya cargada. En CU-10 el filtrado es **server-side** (decisión de producto), así que solo se reutiliza el patrón visual, no la lógica client-side.
- Verificado empíricamente: en el dialecto SQLite de SQLAlchemy, `User.first_name.ilike('%ana%')` compila a `lower(user.first_name) LIKE lower(?)`.

## Goals / Non-Goals

**Goals:**
- Filtrado server-side en `GET /api/users` con `q`/`role`/`active` combinados AND, validados en `services/`, con respuesta de la misma forma y orden que hoy.
- Comportamiento sin criterios idéntico al actual (compatibilidad total con CU-04, CU-05 —que llama `listUsers()` para el selector de estudiantes— y con los smoke existentes).
- Barra de filtros en `UsersPage` sobre el design system, con debounce para el texto, recarga al cambiar selects y «Limpiar filtros».
- Empty state A1 diferenciado (sin resultados vs. sin usuarios registrados) con CTA de limpiar.
- Guardar cada unidad de trabajo en un commit revisable (skill `work-unit-commits`).

**Non-Goals:**
- Modificar modelos o generar migración (no cambia el esquema).
- Paginación, ordenamiento configurable o búsqueda con acentos/tildes a nivel backend.
- Cambiar la forma de la respuesta (sigue siendo el arreglo plano de usuarios serializados) o los endpoints/guards de CU-04.
- Filtrado de otras entidades (cursos, tareas, inscripciones), borrado de usuarios, notificaciones por correo.
- Pantalla nueva de detalle (el modal de edición de CU-04 cubre el paso 6 del flujo).

## Decisions

### D-A: Query params en `GET /api/users` (no body, no endpoint nuevo, no filtrado client-side)
Los criterios viajan como query params (`?q=ana&role=student&active=true`) en el endpoint existente. Alternativas consideradas: (1) **filtrado 100 % client-side** — rechazado porque es decisión de producto (server-side) y porque el listado completo volvería a viajar en cada consulta; (2) **POST de búsqueda con body** — rechazado porque la operación es de solo lectura y los query params son el idiomático HTTP para filtros, cacheables y describibles en la URL; (3) **endpoint nuevo `GET /api/users/search`** — rechazado por duplicar serialización, guards y contrato cuando `GET /api/users` sin criterios ya es «el listado» y el filtrado es una refinación del mismo recurso.

### D-B: Semántica AND y preservación del comportamiento sin criterios
Los criterios presentes se combinan con AND a nivel de `WHERE` acumulativo. Sin criterios (o todos vacíos tras trim) → el query es exactamente el actual (`order_by(User.id)`). Esto preserva el contrato de `user-management` («listar todas las cuentas») y no rompe a los consumidores existentes: `EnrollmentsPage` llama `listUsers()` sin args y filtra client-side por `role === "student" && active`; con parámetros opcionales, esa llamada sigue funcionando sin cambios.

### D-C: `q` con `ilike` parcial sobre nombre, apellido y correo; trim; vacío = sin criterio
`q` se limpia con `.strip()`; si queda vacío se ignora. La coincidencia es parcial e insensible a mayúsculas sobre `first_name`, `last_name` y `email` con `ilike(f"%{q}%")` (OR entre los tres campos). Verificado empíricamente: en SQLite, SQLAlchemy compila `ilike` a `lower(col) LIKE lower(?)`, y SQLite pliega solo ASCII en `lower()`/`LIKE` — por lo que «ANA» coincide con «ana» pero «Álvarez» no se pliega con «álvarez». Se acepta esta limitación (universo chico, sin requisito de folding de acentos en el CU; el normalizado con acentos de CU-05 es client-side y de otro flujo). Escaping de comodines: se usa el patrón parametrizado estándar; los `%`/`_` del usuario quedan como comodines literales del LIKE (comportamiento aceptado y documentado; mitigación opcional de escapar en apply si se desea semántica literal estricta — ver Open Questions).

### D-D: Validación de `role` y `active` en `services/` con `ValidationError` → 400
`role` se valida contra los valores del enum `UserRole` (`student`/`teacher`/`admin`, case-insensitive con `.strip().lower()` como `_parse_role` ya hace para el body de PUT); valor inválido → `ValidationError("El rol es inválido")` → 400. `active` solo acepta los strings `"true"`/`"false"` (query params son strings); cualquier otra cosa —incluido `active` sin valor (`?active=`)— → `ValidationError` → 400 con mensaje claro. Las validaciones viven en el servicio (regla de arquitectura `routes → services`); el blueprint lee los query params, los pasa al servicio y **agrega el `except ValidationError` → 400** que hoy el endpoint de listado no tiene. Alternativa rechazada: validar en el blueprint — violaría la regla de que las validaciones viven en `services/`.

### D-E: Firma de `list_users` con criterios opcionales (backward compatible)
`list_users(q=None, role=None, active=None)` o un dict de criterios opcional; la función sigue siendo la única puerta de consulta del listado. Se reutiliza `ROLE_VALUES` existente. Alternativa rechazada: crear `list_users_filtered` separada — duplicaría el query base y la ordenación; un solo camino con defaults mantiene «sin criterios = comportamiento actual» verificable en un solo lugar.

### D-F: Sin paginación
El universo de usuarios del campus es chico (decisión de producto); la respuesta es el arreglo completo filtrado. Si en el futuro crece, la paginación será un cambio de contrato aparte.

### D-G: Frontend — barra de filtros sobre el `Card` de la tabla, server-side
En `UsersPage.jsx`, una barra de filtros (texto + selects de rol y estado + botón «Limpiar filtros») sobre el `Card` de la tabla, con `FormField` y controles del design system (`form-control`/`form-select`), patrón visual del buscador de CU-05 (`EnrollmentsPage`). Cambios: el texto usa **debounce ~300 ms** antes de recargar; los selects recargan al cambiar; «Limpiar filtros» resetea el estado y recarga sin criterios. `api.js::listUsers` acepta criterios y arma la query string omitiendo los vacíos. `loading`/`error` se manejan como hoy. Alternativa considerada: botón «Buscar» explícito en lugar de debounce — más un clic por consulta; se queda el debounce para paridad de UX con el buscador de CU-05 (que filtra en tiempo real) y se mantiene «Limpiar» como escape explícito.

### D-H: Empty state A1 diferenciado con `EmptyState` y CTA
Cuando hay criterios activos y la respuesta es un arreglo vacío, se renderiza `EmptyState` (icono `bi-search` o `bi-person-x`) con título «No hay resultados para los criterios» y un `Button` «Limpiar filtros» que resetea y recarga. Sin criterios y lista vacía → se conserva el `DataTable` con el mensaje actual «Todavía no hay usuarios registrados.» (o el `EmptyState` equivalente). Se distingue por estado en React (`hasActiveFilters`), no por inferir del contenido. Sigue el precedente de CU-05 que ya diferencia «Sin coincidencias» de «Todos ya inscriptos».

### D-I: Autorización sin cambios (guards actuales)
`@login_required` (401) + `require_roles(UserRole.ADMIN)` (403) ya cubren la autorización del endpoint; no se agregan guards nuevos. Los tests de filtrado re-incluyen 401/403 para fijar que los criterios no relajan la autorización.

### D-J: Sin migración
El cambio no altera modelos ni esquema; solo agrega cláusulas de consulta. No se genera migración Alembic ni se toca `tests/test_migrations.py`. Rollback: revertir los archivos tocados; no hay datos ni esquema que revertir.

### D-K: Registro de decisiones y docs de cierre
Las decisiones de este diseño se registran en `decisiones.md` durante el cierre del CU (siguiendo la numeración vigente), y la fila de `AGENTS.md` de `GET /api/users` se actualiza para documentar los query params.

## Risks / Trade-offs

- **`ilike` en SQLite pliega solo ASCII** → «Álvarez» no matchea «álvarez»; mitigación: aceptado para el universo del TP (D-C), documentado; si se necesita folding de acentos, agregar normalización en el servicio sin tocar el contrato.
- **Comodines `%`/`_` en `q`** → un usuario que escribe `%` usa el comodín del LIKE; impacto mínimo (solo lectura, universo chico); se puede escapar en apply si se quiere semántica literal (Open Question).
- **`EnrollmentsPage` consume `listUsers()`** → los params opcionales no rompen la llamada actual, pero cualquier cambio futuro de firma debe preservar el llamado sin argumentos; mitigado con tests existentes de CU-05 y smoke.
- **Doble fetch en la UI (carga inicial + debounce)** → el debounce puede disparar consultas intermedias; mitigado con el timer de 300 ms y descartando respuestas fuera de orden si se detecta el patrón (precedente: flag `active` en los `useEffect` de CU-05).
- **Volumen del cambio vs. budget de revisión (400 líneas)** → previsiblemente supera el umbral; mitigado con unidades de trabajo/commits encadenados (ver Review Workload Forecast en `tasks.md`) y estrategia `ask-on-risk`.

## Migration Plan

1. Backend: extender `services/user_service.py` (criterios + validaciones) y `blueprints/users.py` (lectura de query params + `except ValidationError` → 400); tests en `backend/tests/test_users.py` (o archivo de filtrado dedicado). Sin migración.
2. Frontend: `features/users/api.js` (criterios en `listUsers`) y `UsersPage.jsx` (barra de filtros, debounce, limpiar, empty state A1) sobre el design system.
3. Verificación: tests del dominio users en iteración; suite completa + `npm run build`/`lint:format` en el gate; `scripts/smoke_cu10.py` vía `scripts/verify.py --cu cu10`; evidencia UI Playwright en `evidencias/cu-10/` (claro/oscuro); revisión (`reviews/cu-10.md`).
4. Cierre: `progreso.md`, `decisiones.md`, fila de API en `AGENTS.md`, archive del cambio openspec; commits por unidad de trabajo.

## Open Questions

- **Escaping de comodines en `q`:** ¿se escapán `%`/`_` para que el texto sea literal (más estricto) o se acepta el comportamiento nativo del LIKE (más simple, D-C)? Se asume sin escaping (nativo) salvo indicación; no cambia specs ni estructura, solo la implementación del `ilike`.
- **Debounce vs. botón «Buscar»:** se asume debounce ~300 ms con «Limpiar filtros» (D-G). Si el usuario prefiere botón explícito, es un ajuste de UI sin cambio de contrato.
