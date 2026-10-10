# Tasks

## 1. Backend — servicio de autenticación y guards

- [x] 1.1 Crear `backend/services/auth_service.py` con `authenticate_user(email, password)` que normaliza el email a minúsculas, busca la cuenta y valida con `check_password_hash`; verificar con un test unitario que devuelve el usuario con credenciales correctas y `None` con incorrectas
- [x] 1.2 Agregar `get_current_user()` (lee `session["user_id"]` y consulta la base) y `logout()` (limpia la sesión) en el service; verificar con tests unitarios que cubren sesión ausente y session id inexistente
- [x] 1.3 Crear `backend/blueprints/guards.py` con los decoradores `login_required` (responde HTTP 401 sin sesión) y `require_roles(*roles)` (deniega con HTTP 403 a rol no autorizado); verificar que el test de `me` sin sesión devuelve 401

## 2. Backend — endpoints de autenticación y sus tests

- [x] 2.1 Implementar `POST /api/auth/login` en `backend/blueprints/auth.py` (devuelve el usuario serializado con su rol, sin password) y verificar tests: 200 login exitoso, 400 campos faltantes, 401 mensaje genérico idéntico para correo inexistente y password incorrecto
- [x] 2.2 Implementar `GET /api/auth/me` (200 con el usuario serializado y su rol; 401 sin sesión) y verificar con tests de ambos escenarios
- [x] 2.3 Implementar `POST /api/auth/logout` (limpia la sesión y responde 200, idempotente) y verificar con tests: logout seguido de `me` → 401, y logout sin sesión → 200 sin error
- [x] 2.4 Ejecutar la suite completa y verificar que `..\.venv\Scripts\python.exe -m pytest -q` (desde `backend/`) pasa todos los tests (21 previos + nuevos)

## 3. Backend — configuración de sesión de la cookie

- [x] 3.1 Configurar en `backend/config/config.py` los flags de cookie (`SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE="Lax"`) y verificar en el test de login que la cookie de sesión se emite con esos atributos
- [x] 3.2 Documentar y mantener `SECRET_KEY` provisto por entorno (default dev-only existente); verificar que `me` autenticado responde correctamente al reiniciar el cliente de test con la misma app (sesión persistente)

## 4. Frontend — cliente de API y formulario de login

- [x] 4.1 Agregar `login`, `getMe` y `logout` a `frontend/src/features/auth/api.js` apuntando a `/api/auth/login|me|logout`; verificar que `cmd /c npm run build` (desde `frontend/`) compila sin errores
- [x] 4.2 Crear `frontend/src/features/auth/LoginForm.jsx` (copy en español neutro, errores del servidor mostrados tal cual, mensaje de éxito) y verificar que el build compila
- [x] 4.3 Agregar el enlace registro→login y login→registro entre `LoginForm` y `RegisterForm`; verificar que el build compila

## 5. Frontend — estado de sesión y cierre de sesión

- [x] 5.1 Agregar a `frontend/src/App.jsx` el estado de usuario actual, restaurarlo con `getMe()` al montar (recarga/refresh) y verificar el build compila
- [x] 5.2 Renderizar `LoginForm` cuando no hay usuario logueado y la barra con rol + botón "Cerrar sesión" cuando lo hay; el cierre llama `logout()` y limpia el estado; verificar el build compila

## 6. Verificación integrada y documentación

- [x] 6.1 Smoke end-to-end: levantar backend y frontend y verificar login 200 + `me` 200 (cookie) + logout 200 + `me` 401 con el mismo cliente HTTP
- [x] 6.2 Actualizar `AGENTS.md` (tabla API con los 3 endpoints y auth requerida), `decisiones.md` (D-011 mecanismo de sesión), `README.md`, `progreso.md` (CU-02 Completada) y `errores.md` si hubo fallas; verificar que cada documento refleja el estado real

## 7. Revisión, archivo y commits

- [x] 7.1 Delegar revisión al subagente `reviewer` (si vuelve a fallar por tier, revisión inline aceptada por el usuario) y corregir los bloqueantes hasta APROBADO; verificar con la misma evidencia de 6.1
- [ ] 7.2 Archivar el cambio openspec (`openspec archive add-user-auth --yes`) y verificar `openspec validate --specs --strict` sin errores
- [ ] 7.3 Registrar tiempos en `tiempos.md` y prompts en `prompts_log.md`, y commitear por unidad de trabajo (conventional commits); verificar `git status` limpio y `git log` coherente