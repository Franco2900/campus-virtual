# AGENTS.md — Backend

Alcance: `backend/`. Las reglas compartidas están en el `AGENTS.md` de la raíz; este archivo no las repite.

## Estructura

```
backend/
├── app.py            # factory: crea la app, registra blueprints, inicializa DB
├── blueprints/       # una por dominio: auth, courses, users, tasks, enrollments, grades, chat, knowledge
├── services/         # lógica de negocio y validaciones
├── models/           # entidades SQLAlchemy
├── config/           # configuración (DB path, secretos por env)
└── migrations/       # migraciones Alembic (Flask-Migrate)
```

## Reglas de la capa

- `routes → services → models`. Lógica de negocio y validaciones en `services/`; nunca en `blueprints/` ni en los modelos.
- Toda consulta a la base pasa por `services/` usando los modelos SQLAlchemy. Sin SQL crudo en `blueprints/`.
- Identidad y permisos SIEMPRE desde la sesión Flask, nunca desde datos que envía el cliente ni desde el modelo.
- Esquema versionado con Flask-Migrate/Alembic (D-023). `db.create_all()` solo para tests (`TESTING`). Un CU que cambie el esquema con datos genera migración (skill `create-migration`); `migrations/` se versiona y queda excluido de ruff.
- Mantener el contrato de respuesta de `docs/api.md` (método, auth y códigos de estado).

## Comandos

- Instalación (una vez): desde la raíz, `python -m venv .venv`; instalar con Windows `.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt` / Linux-macOS `.venv/bin/python -m pip install -r backend/requirements.txt`.
- Dev: Windows `.\.venv\Scripts\python.exe backend\app.py` / Linux-macOS `.venv/bin/python backend/app.py` → `http://127.0.0.1:5000`. SQLite en `backend/instance/campus.db` (`CAMPUS_DB_PATH` lo cambia; `SECRET_KEY` por entorno).
- Migraciones: desde `backend/`, Windows `..\.venv\Scripts\python.exe -m flask --app app db upgrade` / Linux-macOS `../.venv/bin/python -m flask --app app db upgrade`.
- Tests: desde `backend/`, Windows `..\.venv\Scripts\python.exe -m pytest` / Linux-macOS `../.venv/bin/python -m pytest`. En iteración, solo el dominio afectado: `-m pytest tests/test_tasks.py -q`.
- Lint/formato: desde la raíz, Windows `.\.venv\Scripts\python.exe -m ruff check backend` / Linux-macOS `.venv/bin/python -m ruff check backend`, y `-m ruff format --check backend`. Aplicar: `--fix` y `-m ruff format backend`.

## Convenciones

- `snake_case` para variables y funciones, `PascalCase` para clases, archivos en `snake_case`.
- Identificadores en inglés; comentarios solo para decisiones o restricciones no evidentes.
- Ningún endpoint nuevo sin su test en `backend/tests/`.

## Gotchas

- Fallo de Ollama en el chat → 502 con mensaje amable y el turno no se persiste.
- Sin `ollama pull nomic-embed-text`, el alta de fuentes de conocimiento responde 400 y la fila queda en `error`; el resto de la app funciona.
- Fecha límite y estado de corrección (CU-07/CU-08) se validan en `services/`, nunca en el cliente.
