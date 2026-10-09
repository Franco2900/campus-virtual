# Proposal

## Why

El sistema no existe todavía: no hay backend ni frontend. El primer caso de uso aprobado, CU-01 (Registrarse), es la puerta de entrada de todo usuario y el habilitante del resto de los CU. Necesitamos crear la cuenta con correo único y rol Estudiante inicial, y además dejar montado el esqueleto del proyecto (Flask por capas + React/Vite) sobre el que se apoyarán los demás casos de uso.

## What Changes

- Se crea el scaffolding del backend Flask con la arquitectura de capas `routes → services → models` (factory `app.py`, `config/`, `models/`, `services/`, `blueprints/`) y el scaffolding del frontend React + Vite.
- Se incorpora la entidad `User` con: nombre, apellido, correo electrónico (único), contraseña hasheada, rol (Estudiante por defecto) y fecha de creación.
- Se agrega el endpoint `POST /api/auth/register` que valida los datos, verifica la unicidad del correo y crea la cuenta con rol Estudiante.
- Se agrega una pantalla de registro en el frontend que consume dicho endpoint y muestra el resultado (alta confirmada o errores de validación).
- Se define el comando real de ejecución/test y se documenta (AGENTS.md, README, `prompts_log.md`, `progreso.md`, `tiempos.md`).

Fuera de alcance (otros CU): inicio/cierre de sesión y recuperación de contraseña (CU-02), gestión de usuarios y roles (CU-04), filtrado (CU-10). CU-01 no autentica ni emite sesión/token.

## Capabilities

### New Capabilities
- `user-auth`: registro de cuentas de usuario (CU-01). Cubre la creación de la cuenta con correo único, la asignación del rol Estudiante inicial y las validaciones de los datos de registro.

### Modified Capabilities
<!-- Ninguna: no hay specs previas. -->

## Impact

- **Código nuevo:** `backend/` (app, config, models, services, blueprints/auth), `frontend/` (scaffold Vite, cliente API, pantalla de registro), `backend/tests/`.
- **API:** nuevo `POST /api/auth/register` (se registra en la tabla de API de `AGENTS.md`).
- **Dependencias:** backend Flask 3.1.x, Flask-SQLAlchemy 3.1.x, SQLAlchemy 2.0.x, pytest; frontend Vite 7 + React 19. Hashing con `werkzeug.security` (sin dependencia extra). Sin `flask-cors` (se usa proxy de Vite en desarrollo).
- **Base de datos:** SQLite vía SQLAlchemy; esquema inicial creado con `db.create_all()` desde el factory.
- **Reglas de negocio:** correo como identificador único; cada usuario con exactamente un rol; los nuevos usuarios reciben rol Estudiante.
- **Proceso:** define por primera vez los comandos reales de ejecución y test del proyecto.
