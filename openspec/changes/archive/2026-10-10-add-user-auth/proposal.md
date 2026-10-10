# Proposal

## Why

Un usuario registrado (CU-01) no puede iniciar sesión ni cerrarla: no existe autenticación, y los casos de uso CU-03 a CU-10 exigen como precondición que "el usuario inició sesión". Necesitamos establecer el mecanismo de sesión y el acceso por rol que hereda el resto del sistema.

## What Changes

- Agregar autenticación por credenciales: `POST /api/auth/login` valida correo y contraseña e inicia una sesión.
- Establecer sesión por cookie firmada de Flask (itsdangerous) con `SECRET_KEY` provista por entorno (sin default en producción).
- Exponer la sesión actual: `GET /api/auth/me` devuelve el usuario autenticado y su rol.
- Permitir cerrar sesión: `POST /api/auth/logout` invalida la sesión activa.
- Rechazar credenciales inválidas con un único mensaje genérico (HTTP 401) sin revelar cuál credencial falló.
- Robustecer el contrato de acceso por rol: helpers `login_required` y verificación de rol reutilizables por los próximos CU.
- Frontend: pantalla de inicio de sesión, restauración de sesión al recargar y botón de cierre en el estado de sesión.
- Fuera de alcance (registrado como pendiente): recuperación de contraseña (A2), requiere infraestructura de envío de correo inexistente en el stack.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `user-auth`: agrega requirements de autenticación de credenciales, sesión activa, consulta de sesión actual y cierre de sesión, manteniendo los existentes de registro.

## Impact

- **Backend:** `backend/blueprints/auth.py` (nuevos endpoints), nuevo `backend/services/auth_service.py`, blueprint o helper de protección `login_required`, `backend/config/config.py` (`SECRET_KEY` obligatorio vía entorno). Sin cambios de esquema ni migración (se reutiliza `User.password_hash`).
- **Dependencias:** ninguna nueva (sesión por cookie firmada, ya incluida en Flask/Werkzeug).
- **Tests:** ampliación de `backend/tests/test_register.py` o nuevo `test_auth.py` (login exitoso, credenciales inválidas, campos faltantes, `me` sin sesión, logout).
- **Frontend:** `src/features/auth/LoginForm.jsx`, estado de sesión en `src/App.jsx`, API `login`/`logout`/`me` en `src/features/auth/api.js`.
- **Docs:** tabla de API en `AGENTS.md`, `decisiones.md` (D-011 mecanismo de sesión), `progreso.md`, `tiempos.md`, `prompts_log.md`, README.