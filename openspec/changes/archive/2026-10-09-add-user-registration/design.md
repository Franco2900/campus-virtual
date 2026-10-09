# Design

## Context

Ver `proposal.md` — Why. Punto de partida: repo con documentación y openspec inicializado, pero sin código. No hay `backend/` ni `frontend/`, no hay comandos de ejecución/test definidos, y `casos_de_uso.md` / `AGENTS.md` fijan la arquitectura de capas y las reglas de negocio. Este diseño fija el esqueleto del proyecto y las decisiones técnicas que el resto de los CU reutilizarán.

Restricciones relevantes:
- Python 3.14.6 (muy nuevo) y Node v24.19.0.
- En Windows, `npm` y `openspec` se invocan vía `cmd /c` por la execution policy de PowerShell.
- Portabilidad Windows/Linux/macOS: rutas relativas y sin comandos exclusivos de una plataforma en el código de la app.

## Goals / Non-Goals

**Goals:**
- Dejar el scaffolding de backend y frontend listo para escalar a los 10 CU.
- Implementar CU-01 end-to-end (modelo → servicio → blueprint → pantalla → cliente API).
- Fijar los comandos reales de instalación, ejecución y test.
- Contrato de API estable para `POST /api/auth/register`.

**Non-Goals:**
- Autenticación, sesión/token, cierre de sesión y recuperación de contraseña (CU-02).
- Asignación de roles por Administrador (CU-04).
- Migraciones de esquema formales (el esquema recién nace; se usa `create_all`).
- Autenticación/autorización en el endpoint de registro: registrar es una operación pública.

## Decisions

### D-A. Estructura backend por capas
```
backend/
├── app.py                 # create_app(): app factory
├── config/
│   └── config.py          # configuración por entorno (DB path, secret)
├── models/
│   ├── base.py            # db = SQLAlchemy()
│   └── user.py            # User
├── services/
│   ├── errors.py          # excepciones de dominio (ValidationError, ConflictError)
│   └── user_service.py    # register_user(): validaciones + persistencia
├── blueprints/
│   └── auth.py            # POST /api/auth/register
├── tests/
│   ├── conftest.py
│   └── test_register.py
└── requirements.txt
```
**Por qué:** replica la regla `routes → services → models`. Las validaciones de negocio viven en `services/user_service.py`; el blueprint solo traduce HTTP ↔ servicio; el modelo no tiene lógica de negocio.
**Alternativas:** MVC de un solo archivo (descartada: se degrada con 10 CU); Hexagonal (descartada por ceremonia excesiva).

### D-B. Tipos del dominio: rol y errores
- Rol como `enum` de Python (`UserRole.STUDENT = "student"`, `TEACHER`, `ADMIN`) persistido como string. Rol por defecto Estudiante.
- Errores de dominio `ValidationError` y `ConflictError` definidos en `services/errors.py`; el blueprint los mapea a HTTP 400 y 409. **Por qué:** evita que el servicio conozca HTTP y mantiene la lógica en la capa correcta.

### D-C. Hasheo de contraseña
`werkzeug.security.generate_password_hash` / `check_password_hash`.
**Por qué:** ya viene con Flask, es puro Python (evita problemas de compilación de `bcrypt` en Python 3.14 en Windows) y `check_password_hash` será reutilizado por CU-02.
**Alternativas:** `passlib` + `bcrypt` (descartada: dependencia extra y posible falta de wheel en 3.14).

### D-D. Correo único insensible a mayúsculas
El correo se normaliza a minúsculas y se guarda en una columna `email` con `unique=True, nullable=False`.
**Por qué:** cumple "identificador único"; la comparación case-insensitive evita duplicados por capitalización. La unicidad se verifica en el servicio (mensaje de negocio) y se respalda con la restricción UNIQUE (integridad).

### D-E. Inicialización de esquema
`db.create_all()` dentro de `create_app()`.
**Por qué:** el esquema nace ahora y no hay datos que migrar; mantiene el bootstrap simple y portable.
**Alternativas:** Flask-Migrate/Alembic (postergada: se introducirá cuando un CU cambie un esquema existente con datos, vía skill `create-migration`).

### D-F. Configuración por entorno y base de datos
- `config.py` lee de variables de entorno con defaults seguros: `CAMPUS_DB_PATH` (default `backend/instance/campus.db` resuelto relativo al proyecto) y `SECRET_KEY` (default de desarrollo, nunca un secreto real en el repo).
- SQLite vía SQLAlchemy con `SQLALCHEMY_DATABASE_URI=sqlite:///<ruta relativa>`.
**Por qué:** cumple "sin secretos en el código" y "rutas relativas"; permite override en CI/test.

### D-G. Contrato de API
`POST /api/auth/register` — público (no requiere auth).
- Request JSON: `{ "first_name", "last_name", "email", "password" }`.
- 201: `{ "id", "first_name", "last_name", "email", "role" }` (sin contraseña).
- 400: `{ "error": "..." }` (campos faltantes, email inválido, contraseña corta).
- 409: `{ "error": "..." }` (email ya registrado).
- Longitud mínima de contraseña: 8 caracteres.

### D-H. CORS resuelto con proxy de desarrollo de Vite
El frontend define en `vite.config.js` un proxy `/api → http://localhost:5000`.
**Por qué:** evita `flask-cors` (dependencia extra) y mantiene el backend mínimo; en producción el frontend puede servirse detrás del mismo origen.

### D-I. Estructura frontend por feature
```
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── api/
    │   └── client.js          # fetch wrapper base
    └── features/
        └── auth/
            ├── api.js         # registerUser()
            └── RegisterForm.jsx
```
**Por qué:** organización por feature escala a los 10 CU sin una carpeta `components/` genérica que se vuelva bolsa de gato. Las validaciones de servidor son la fuente de verdad; el cliente solo muestra errores.

### D-J. Estrategia de test
`pytest` con la app creada en modo test sobre una base SQLite en memoria o archivo temporal (`app.config` override), y el test client de Flask. Casos: alta exitosa, email duplicado, email con formato inválido, campos faltantes, contraseña corta, rol=Estudiante por defecto, contraseña no devuelta.
**Por qué:** `strict_tdd: false` (no hay runner aún), pero el primer CU instala el runner y deja la base de tests.

### D-K. Comandos reales (a documentar)
- Backend: crear venv, `pip install -r backend/requirements.txt`, ejecutar `python backend/app.py`.
- Frontend: `cmd /c npm install`, `cmd /c npm run dev`, `cmd /c npm run build` (en Windows; en Linux/macOS sin el prefijo).
- Tests: `python -m pytest` (desde `backend/`).

## Risks / Trade-offs

- **Python 3.14.6 muy nuevo** → alguna rueda binaria puede faltar. Mitigación: `werkzeug` (puro Python), `SQLAlchemy`/`Flask-SQLAlchemy` en versiones recientes con soporte 3.14; si `pip install` falla, registrar en `errores.md` y ajustar versión.
- **`create_all` sin migraciones** → si un CU posterior cambia el esquema con datos, hay que introducir Alembic. Mitigación: documentado como deuda consciente; skill `create-migration` cuando ocurra.
- **`SECRET_KEY` con default de desarrollo** → válido solo en dev. Mitigación: exigir override por entorno antes de cualquier despliegue; se documenta.
- **Proxy de Vite solo en desarrollo** → en producción se debe servir el frontend desde el mismo origen o configurar proxy inverso. Mitigación: documentado; no afecta CU-01.
- **Registro público sin rate limiting** → fuera de alcance del TP; se anota como no-goal.

## Migration Plan

No aplica (no hay datos ni esquema previo). Rollback: eliminar `backend/`, `frontend/` y los artefactos de CU-01; el cambio no toca datos existentes.

## Open Questions

- Ninguna que afecte specs, enfoque o tareas. El mecanismo de sesión/token se decide en CU-02.
