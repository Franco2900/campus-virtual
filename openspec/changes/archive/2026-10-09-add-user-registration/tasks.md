# Tasks

## 1. Scaffolding del backend

- [x] 1.1 Crear `backend/requirements.txt` con Flask 3.1.x, Flask-SQLAlchemy 3.1.x, SQLAlchemy 2.0.x y pytest; verificar con `python -m pip install -r backend/requirements.txt` (crear antes el venv).
- [x] 1.2 Crear el esqueleto `backend/` (`app.py`, `config/config.py`, `models/`, `services/`, `blueprints/`, `tests/`) respetando `routes → services → models`; verificar que `create_app()` importa y arranca (`python backend/app.py` levanta sin error).
- [x] 1.3 Definir `config.py` con override por variables de entorno (`CAMPUS_DB_PATH`, `SECRET_KEY`) y default relativo al proyecto; verificar que no hay rutas absolutas ni secretos reales en el archivo.

## 2. Modelo User y esquema

- [x] 2.1 Implementar `models/base.py` (`db = SQLAlchemy()`) y `models/user.py` (`User` con nombre, apellido, email único, password_hash, role, created_at) y el enum `UserRole` con default Estudiante; verificar que `db.create_all()` crea la tabla `user`.
- [x] 2.2 Verificar contra el esquema real que `email` es `NOT NULL` + `UNIQUE` y que no se almacena contraseña en texto plano (inspección del esquema generado).

## 3. Servicio de registro

- [x] 3.1 Implementar `services/errors.py` (`ValidationError`, `ConflictError`) y `services/user_service.py` con `register_user()`: validación de campos, formato de email, longitud mínima de contraseña (8), normalización a minúsculas, chequeo de email único, hasheo con `werkzeug.security` y rol Estudiante forzado; verificar que la lógica vive solo en `services/`.
- [x] 3.2 Escribir tests de servicio en `backend/tests/` (alta OK con rol Estudiante, email duplicado → error, email inválido → error, campos faltantes → error, contraseña corta → error, contraseña no almacenada en claro); verificar con `python -m pytest` desde `backend/` que pasan.

## 4. Endpoint POST /api/auth/register

- [x] 4.1 Implementar `blueprints/auth.py` (público, sin auth) que mapea `ValidationError → 400` y `ConflictError → 409`, devuelve 201 con la cuenta sin contraseña, y registrarlo en `create_app()`; verificar con el test client que el endpoint responde según el contrato (201/400/409).
- [x] 4.2 Agregar tests de endpoint (alta 201 sin `password` en el body, duplicado 409, inválido 400, rol ignorado → Estudiante); verificar con `python -m pytest` que pasan.

## 5. Scaffolding del frontend y cliente de API

- [x] 5.1 Crear el proyecto Vite + React (`frontend/` con `package.json`, `vite.config.js`, `index.html`, `src/main.jsx`, `src/App.jsx`) y configurar el proxy `/api → http://localhost:5000`; verificar con `cmd /c npm install` y `cmd /c npm run build` (en Linux/macOS sin el prefijo `cmd /c`).
- [x] 5.2 Implementar `src/api/client.js` (wrapper fetch base) y `src/features/auth/api.js` (`registerUser()`); verificar que compila en el build y respeta el contrato `POST /api/auth/register`.

## 6. Pantalla de registro

- [x] 6.1 Implementar `src/features/auth/RegisterForm.jsx` (campos nombre, apellido, email, contraseña) que consume `registerUser()` y muestra éxito o errores de validación provistos por el backend; verificar con `cmd /c npm run build` que compila sin errores.
- [x] 6.2 Smoke end-to-end manual/dev: levantar backend y frontend y confirmar un alta exitosa y un error de email duplicado (registrar el comando exacto en el resumen de la tarea).

## 7. Documentación y verificación de integración

- [x] 7.1 Actualizar `AGENTS.md` ("Cómo ejecutar" con comandos reales + tabla de API con `POST /api/auth/register`) y `README.md` (instalación/ejecución/testing/estructura); verificar que los comandos documentados se ejecutan tal cual.
- [x] 7.2 Registrar decisiones en `decisiones.md` (versiones del stack, hashing Werkzeug, `create_all`, proxy Vite) y actualizar `progreso.md` (CU-01) y `prompts_log.md`; verificar que reflejan el estado real.
- [x] 7.3 Ejecutar `run-verification`: `python -m pytest` (backend) + `cmd /c npm run build` (frontend) + smoke de registro; registrar comandos y resultados reales.
- [x] 7.4 Revisión obligatoria con el subagente `reviewer`; corregir bloqueantes hasta APROBADO.
- [x] 7.5 Sincronizar specs (`openspec sync-specs`/`/opsx-sync`) y archivar el cambio (`/opsx-archive`); verificar que `openspec/` queda consistente y el cambio movido a `changes/archive/`.
