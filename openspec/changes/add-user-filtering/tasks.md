# Tasks

## 1. Backend — Servicio y endpoint de filtrado de usuarios

- [x] 1.1 **Extender `backend/services/user_service.py::list_users`** con criterios opcionales (`q`, `role`, `active`) según D-B/D-C/D-E: trim de `q` (vacío = sin criterio), `ilike(f"%{q}%")` OR sobre `first_name`/`last_name`/`email`, igualdad sobre `role`/`active`, combinación AND y `order_by(User.id)` preservado. Sin criterios el query debe ser el actual. Verificación: `..\.venv\Scripts\python.exe -m pytest tests/test_users.py -q` (o el archivo de filtrado nuevo) pasa incluyendo los tests de 1.3.
- [x] 1.2 **Implementar las validaciones de criterios en el servicio** (D-D): `role` contra `ROLE_VALUES` (case-insensitive) → `ValidationError`; `active` solo `"true"`/`"false"` (también `?active=` sin valor) → `ValidationError`; mensaje en español claro. Verificación: cubierto por los tests de 1.3 (`role` inválido, `active` inválido, criterio inválido junto a uno válido).
- [x] 1.3 **Agregar tests backend del filtrado** (extender `backend/tests/test_users.py` o crear `backend/tests/test_users_filtering.py`) cubriendo los escenarios de la spec: sin criterios (comportamiento actual), `q` parcial case-insensitive sobre nombre/apellido/correo, `q` en blanco, `role`, `active`, combinados AND, 400 con `role`/`active` inválidos (y el precedence del 400 sobre resultados parciales), 401 sin sesión, 403 no-Admin con y sin criterios, y que la consulta filtrada no modifica datos. Verificación: `..\.venv\Scripts\python.exe -m pytest tests/test_users*.py -q` pasa.
- [x] 1.4 **Actualizar `backend/blueprints/users.py::list_users_endpoint`** (D-A/D-D): leer `request.args` (`q`, `role`, `active`), pasarlos al servicio y agregar `except ValidationError` → 400 con `{"error": ...}` (los guards `@login_required`/`@require_roles(ADMIN)` no cambian). Verificación: `GET /api/users?role=superuser` responde 400 y `GET /api/users` sin params responde 200 como antes (tests de 1.3).
- [x] 1.5 **Actualizar la fila de `GET /api/users` en la tabla de API de `AGENTS.md`** documentando los query params opcionales `q`/`role`/`active` (CU-10). Verificación: la fila refleja method, ruta, CU y params correctos.
- [x] 1.6 **Lint y formato backend**: `.\.venv\Scripts\python.exe -m ruff check backend` y `-m ruff format --check backend`. Verificación: sin errores.
- [x] 1.7 **Commit unidad 1 (work-unit):** `feat(users): add server-side filtering to GET /api/users` — servicio + blueprint + tests + fila de API, tests incluidos en el mismo commit. Verificación: el repo es consistente aplicando solo este commit (CU-04 y CU-05 siguen verdes).

## 2. Frontend — Barra de filtros y estado vacío A1

- [x] 2.1 **Extender `frontend/src/features/users/api.js::listUsers`** para aceptar criterios opcionales `{ q, role, active }` y armar la query string omitiendo los vacíos (D-A/D-G). Verificación: `cmd /c npm run build` compila y la llamada sin argumentos sigue siendo `GET /api/users`.
- [x] 2.2 **Implementar la barra de filtros en `UsersPage.jsx`** (D-G): `FormField` + `input type="search"` para `q` con debounce ~300 ms, `select` de rol (todos/Estudiante/Profesor/Administrador), `select` de estado (todos/activos/inactivos), botón «Limpiar filtros»; recarga server-side al cambiar cualquier criterio; `data-testid` estables para la evidencia (`users-filter-q`, `users-filter-role`, `users-filter-active`, `users-filter-clear`). Reutilizar `Card`, `Button`, `FormField` del design system; sin colores hardcodeados. Verificación: cambiar un select o tipear texto (tras el debounce) recarga la tabla con el resultado del backend.
- [x] 2.3 **Implementar el estado vacío A1 diferenciado** (D-H): con criterios activos y respuesta vacía, `EmptyState` con ícono, mensaje «No hay resultados para los criterios» y CTA «Limpiar filtros»; sin criterios y lista vacía, conservar «Todavía no hay usuarios registrados.». Verificación: con un `q` sin coincidencias se ve el empty state A1 con CTA; con la base sin usuarios y sin filtros se ve el mensaje original.
- [x] 2.4 **Build y formato frontend**: dentro de `frontend/`, `cmd /c npm run build` y `cmd /c npm run lint:format`. Verificación: build exitoso y sin errores de Prettier.
- [x] 2.5 **Commit unidad 2 (work-unit):** `feat(users): add filter bar with A1 empty state to UsersPage` — `api.js` + `UsersPage.jsx`. Verificación: el repo es consistente aplicando solo este commit (la pantalla de usuarios funciona sin filtros como antes).

## 3. Verificación HTTP, evidencia UI y revisión

- [x] 3.1 **Crear `scripts/smoke_cu10.py`** (patrón `smoke_cu09.py`) y conectarlo a `scripts/verify.py`: Admin filtra por `q`, `role`, `active` y combinados (200 + resultados esperados), `q` en blanco, 400 con `role`/`active` inválidos, 401 sin sesión, 403 no-Admin. Verificación: `.\.venv\Scripts\python.exe scripts\verify.py --cu cu10` pasa.
- [x] 3.2 **Suite backend completa y gate de cierre**: dentro de `backend/`, `..\.venv\Scripts\python.exe -m pytest`. Verificación: suite completa sin fallas nuevas.
- [x] 3.3 **Evidencia UI (Playwright)**: con `scripts/verify.py --serve`, capturar en `evidencias/cu-10/` los estados clave en tema claro y oscuro: listado sin filtros, filtrado con resultados (texto + rol + estado), A1 sin resultados con CTA de limpiar y limpieza de filtros; consola sin errores inesperados. Verificación: screenshots estandarizados `NN-accion.png` presentes; gate de evidencia cumplido.
- [x] 3.4 **Revisión del CU-10**: ejecutar el subagente `reviewer` (o la skill `review-use-case` inline si no está disponible) y persistir `reviews/cu-10.md` con hallazgos (`archivo:línea`, severidad), veredicto y mapa de evidencia. Verificación: veredicto APROBADO sin bloqueantes, o corrección de bloqueantes antes de cerrar.
- [x] 3.5 **Commit unidad 3 (work-unit):** `test(users): add cu10 smoke script and UI evidence` — smoke + evidencia de `evidencias/cu-10/`. Verificación: `verify.py --cu cu10` reproduce los checks desde cero.

## 4. Documentación y cierre del CU-10

- [ ] 4.1 **Actualizar documentación de cierre**: `progreso.md` (CU-10 Completado + resumen), `decisiones.md` (decisiones del filtrado siguiendo la numeración vigente), `README.md` si corresponde (features/API). Verificación: los archivos reflejan el CU-10 implementado y verificado.
- [ ] 4.2 **Archivar el cambio openspec** (`cmd /c openspec archive add-user-filtering` siguiendo la skill `openspec-archive-change`) y verificar que la capacidad `user-filtering` queda en `openspec/specs/`. Verificación: `openspec list --specs` muestra `user-filtering`.
- [ ] 4.3 **Commit unidad 4 (work-unit):** `docs(users): close cu-10 with progress and decisions` — docs + artefactos del archive. Verificación: diff solo de documentación/archivo, sin código de app.

## Review Workload Forecast

- **Estimación de líneas cambiadas (additions + deletions, sin archivos generados):** ~450-620 líneas.
  - Backend: `services/user_service.py` (~55-75), `blueprints/users.py` (~15-20), `tests/test_users*.py` (~160-220), `AGENTS.md` (+1).
  - Frontend: `features/users/api.js` (~10-15), `UsersPage.jsx` (~85-120).
  - Scripts/docs: `scripts/smoke_cu10.py` (~90-120) + hook en `verify.py` (~5), `reviews/cu-10.md` (~60), `progreso.md`/`decisiones.md`/`README.md` (~30-50).
- **Chained PRs recommended:** Sí. El volumen estimado supera el umbral de revisión cómoda (~400 líneas). Unidades revisables encadenadas (coinciden con los commits de las secciones 1-4):
  1. Backend: servicio + validaciones + endpoint + tests + fila de API.
  2. Frontend: barra de filtros + empty state A1.
  3. Verificación y evidencia: smoke CU-10 + screenshots + `reviews/cu-10.md`.
  4. Docs de cierre + archive.
  Cada unidad mantiene tests/docs con su código y es revisable/mergeable por separado.
- **400-line budget risk:** Sí — la estimación (~450-620) excede el budget de 400 líneas por PR; sin cambios de esquema (no hay migración), lo que reduce el riesgo de la unidad de backend.
- **Decision needed before apply (delivery strategy `ask-on-risk``):** Sí — confirmar antes de implementar: (a) proceder con la cadena de 4 unidades/PRs recomendada; (b) aceptar algún `size:exception` si tras el corte honesto alguna unidad queda por encima del budget; y (c) las Open Questions de `design.md` (escaping de comodines en `q`; debounce vs. botón «Buscar»).
