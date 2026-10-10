# Design

## Context

CU-01 dejó registro funcional (`POST /api/auth/register`, hash de contraseña con Werkzeug, rol Estudiante forzado) pero sin autenticación. `User.password_hash` ya existe en el esquema, así que este cambio no toca la base. Todos los CU-03 a CU-10 tienen como precondición "usuario inició sesión" y acceso por rol. Ver proposal.md - Why.

## Goals / Non-Goals

**Goals:**
- Sesión de usuario por cookie firmada de Flask (itsdangerous), sin dependencias nuevas.
- Contrato de autenticación estable: `login` / `me` / `logout` que heredan los próximos CU.
- Helpers de protección por rol reutilizables (`login_required`, verificación de rol).
- Un único mensaje genérico ante credenciales inválidas (no revelar cuál falló).

**Non-Goals:**
- Recuperación de contraseña (A2): fuera de alcance (requiere servicio de correo inexistente en el stack). Registrada como pendiente.
- CSRF hardening: diferido (deuda técnica documentada, asumible para el TP por SameSite=Lax y proxy mismo-origen).
- Gestión de usuarios ni roles (CU-04): solo se exponen datos del usuario autenticado.
- Sin cambios de esquema ni migraciones.

## Decisions

- **D-A — Mecanismo de sesión: cookie firmada de Flask (itsdangerous).** Decidido por el usuario (D-011 en `decisiones.md`). La sesión vive en una cookie `HttpOnly` + `SameSite=Lax` firmada con `SECRET_KEY`; Flask la gestiona vía `flask.session`. Alternativas consideradas y descartadas en CU-02 plan: (a) JWT stateless con PyJWT en `Authorization` header y `localStorage` (más piezas móviles, dependencia nueva, riesgo de XSS en storage, sin sentido mientras el frontend es servido por el mismo origen en dev); (b) Flask-Session server-side (guardar sesiones en el servidor: más robusto para invalidación inmediata y revocación, pero agrega dependencia y estado; sobre-ingeniería para el alcance del TP).
- **D-B — `SECRET_KEY` obligatorio vía entorno fuera de desarrollo.** Se mantiene el default dev-only existente solo cuando no se requiere producción; se documenta que en cualquier entorno real debe fijarse `SECRET_KEY` (sin secretos en el repo). La verificación de presencia se hace en `config.py` (si el entorno lo exige, fallar temprano), no en los endpoints.
- **D-C — Endpoints y flujo.** `POST /api/auth/login` valida credenciales en la capa service, aloja el `user_id` en `session` y devuelve el serializado del usuario con su rol (HTTP 200). `GET /api/auth/me` devuelve el usuario de la sesión con su rol o HTTP 401 si no hay sesión. `POST /api/auth/logout` limpia la sesión y responde 200 siempre (idempotente, incluso sin sesión). Todos los payloads reutilizan la serialización de CU-01 (sin contraseña ni hash).
- **D-D — Capas y helpers.** `services/auth_service.py` concentra la lógica: `authenticate_user(email, password)` (busca por email normalizado a minúsculas como en registro y verifica con `check_password_hash`), `get_current_user()` (lee `session["user_id"]` y consulta la base), `logout()` (limpia la sesión). El decorador `login_required` y el guard de roles viven en `blueprints/guards.py` (módulo compartido de blueprints) y se apoyan en el service; así la regla `routes → services → models` se mantiene y los próximos blueprints (courses, users, tasks…) solo importan el guard.
- **D-E — Mensaje genérico de credenciales inválidas.** Tanto un correo inexistente como una contraseña incorrecta responden HTTP 401 con el mismo texto ("Correo electrónico o contraseña incorrectos"). No se diferencia el caso para no facilitar enumeración de cuentas; tampoco se revela en logs.
- **D-F — Frontend: sesión nativa y estado.** El login se hace con el cliente API existente a las mismas rutas proxeadas (`/api/...`); como el proxy de Vite hace mismo-origen en dev, la cookie de sesión viaja automáticamente sin cambios de CORS ni `credentials` explícito. `src/App.jsx` mantiene el estado del usuario actual, se restaura con `GET /api/auth/me` al montar (recarga/refresco) y ofrece formulario de login y botón de logout; `RegisterForm` ya existente queda como acceso alternativo a login.
- **D-G — Tests.** Suite de pytest con cliente de pruebas: login exitoso (200 + rol + sin password), correo inexistente (401 genérico), password incorrecto (401 genérico e idéntico mensaje), campos faltantes (400), `me` con y sin sesión (200/401), logout seguido de `me` (401), logout sin sesión (200). Se reutilizan los helpers del `conftest.py` de CU-01 para crear usuarios.

## Risks / Trade-offs

- [Cookie de sesión no listable/invalidable inmediatamente desde el servidor] → Aceptable para el TP; las tareas por rol y el logout por cookie cubren CU-03..CU-10; si más adelante se necesita revocación activa, migrar a Flask-Session (alternativa D-A) sin tocar el contrato de endpoints.
- [XSRF/CSRF sobre cookies] → Mitigación parcial: `SameSite=Lax` (bloquea cross-site en navegadores modernos) y frontend mismo-origen vía proxy. Documentado como deuda técnica, no bloqueante para el alcance.
- [Riesgo de exponer el rol → control de acceso por rol] → El guard de roles (`require_roles`) se aplicará a cada endpoint protegido de los próximos CU; `me` solo devuelve el rol del propio usuario.
- [Enumeración de cuentas] → Mitigada por D-E.

## Migration Plan

No aplica migración de esquema. Despliegue: fijar `SECRET_KEY` en el entorno (ya soportado por `config.py` desde CU-01). Rollback: quitar los tres endpoints y el desempaquetado de sesión; el registro sigue funcionando intacto.

## Open Questions

Ninguna que afecte specs, enfoque o tareas (recuperación de contraseña y CSRF quedan registrados como pendientes, no como preguntas abiertas de este cambio).