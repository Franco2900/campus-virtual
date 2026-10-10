# Campus Virtual

Sistema web de gestión académica (campus virtual) con tres roles —Estudiante, Profesor y Administrador— y un asistente conversacional integrado.

Trabajo Práctico Integrador — Curso IA (UNLa) — Grupo 12.

## Vista previa

> PENDIENTE DE DEFINIR: capturas de la aplicación una vez implementada.

## Características

- Registro y autenticación de usuarios (**CU-01 y CU-02 implementados**): alta de cuenta, login con cookie de sesión firmada, sesión actual, cierre de sesión.
- Gestión de cursos, usuarios e inscripciones (CU-03, CU-04, CU-05).
- Gestión de tareas, entregas y correcciones (CU-06, CU-07, CU-08).
- Consulta de calificaciones y filtrado de usuarios (CU-09, CU-10).
- Chatbot asistente integrado con LangChain + Ollama.

## Tecnologías

| Área | Tecnología |
|------|-----------|
| Backend | Python + Flask |
| Frontend | React + Vite (Node) |
| Base de datos | SQLite |
| ORM | SQLAlchemy |
| Chatbot | LangChain + Ollama (local) |

Las versiones exactas están en `backend/requirements.txt` (backend) y `frontend/package.json` (frontend).

## Requisitos previos

- Python 3.14 (verificado en 3.14.6) y `pip`.
- Node.js v24 (verificado en v24.19.0) y `npm`.
- En Windows, `npm` se invoca como `cmd /c npm ...` por la execution policy de PowerShell.

## Instalación

```bash
# Backend (desde la raíz del proyecto)
python -m venv .venv
# Windows
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
# Linux/macOS
.venv/bin/python -m pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install        # Windows: cmd /c npm install
```

## Ejecución

```bash
# Backend (desde la raíz) → http://127.0.0.1:5000
python backend/app.py

# Frontend (desde frontend/) → http://localhost:5173
npm run dev        # Windows: cmd /c npm run dev
```

El servidor de desarrollo de Vite proxea `/api` hacia `http://localhost:5000`.

## Testing

```bash
# Backend (desde backend/)
..\.venv\Scripts\python.exe -m pytest        # Linux/macOS: ../.venv/bin/python -m pytest

# Frontend (desde frontend/)
npm run build                                 # Windows: cmd /c npm run build

# Smoke end-to-end (arranca servicios, valida y limpia; por defecto CU-02)
..\.venv\Scripts\python.exe scripts\verify.py                 # Linux/macOS: .venv/bin/python ...
..\.venv\Scripts\python.exe scripts\verify.py --diagnose     # estado de puertos/pids (read-only)
..\.venv\Scripts\python.exe scripts\verify.py --cu cu03      # requiere scripts/smoke_cu03.py
```

## Estructura

```
/
├── AGENTS.md          # instrucciones para agentes de IA
├── README.md          # este archivo
├── opencode.json      # configuración de proyecto (MCP, permisos)
├── casos_de_uso.md    # especificación de los 10 casos de uso
├── decisiones.md      # registro de decisiones
├── errores.md         # bitácora de errores
├── progreso.md        # control de progreso
├── prompts_log.md     # auditoría de prompts
├── tiempos.md         # medición de tiempos
├── openspec/          # specs spec-driven (fuente de verdad de specs)
├── backend/           # API Flask (app.py, config/, models/, services/, blueprints/, tests/)
└── frontend/          # SPA React + Vite (src/api/, src/features/)
```

## API

| Método | Ruta | CU | Propósito | Auth |
|--------|------|----|-----------|------|
| POST | `/api/auth/register` | CU-01 | Registrar una cuenta (rol Estudiante) | Público |
| POST | `/api/auth/login` | CU-02 | Iniciar sesión (emite cookie de sesión) | Público |
| GET | `/api/auth/me` | CU-02 | Obtener el usuario autenticado | Sesión |
| POST | `/api/auth/logout` | CU-02 | Cerrar sesión (idempotente) | Sesión |

## Configuración

Variables de entorno (con valores por defecto para desarrollo):

- `CAMPUS_DB_PATH`: ruta del archivo SQLite (default `backend/instance/campus.db`).
- `SECRET_KEY`: clave de sesión (default solo de desarrollo; fijar en producción).

## Servidores MCP (Model Context Protocol)

El desarrollo se apoya en tres servidores MCP. La configuración vive en `opencode.json` (proyecto) y en la config global de opencode (`~/.config/opencode/opencode.jsonc`).

| Servidor | Tipo | Origen | Rol en el desarrollo |
|----------|------|--------|----------------------|
| `engram` | Memoria (local) | Config global | Memoria persistente del proyecto: decisiones, gotchas y estado que sobreviven entre sesiones y a la compactación de contexto. |
| `context7` | Documentación (remoto/externo) | Config global | Documentación actualizada de Flask, SQLAlchemy, React, Vite, LangChain y Ollama; reduce APIs alucinadas por el modelo. Es el MCP externo requerido por la consigna. |
| `filesystem` | Filesystem (local) | `opencode.json` (proyecto) | Acceso a archivos acotado por allowlist a la carpeta del proyecto. Valor demostrativo del protocolo; opencode ya dispone de acceso a archivos nativo. |
| `playwright` | Browser e2e (local) | `opencode.json` (proyecto) | Validación real de la UI por CU: navegar, completar formularios y capturar screenshots como evidencia verificable (`@playwright/mcp`, headless + chromium). Complementa, no reemplaza, a pytest y al smoke HTTP. |

- **Terminal:** se resuelve con la herramienta nativa de opencode (no se usa un MCP de terminal, por no existir un servidor oficial maduro).
- **Comando del MCP filesystem:** `cmd /c npx -y @modelcontextprotocol/server-filesystem "<ruta del proyecto>"`.
- **Portabilidad:** la ruta del MCP filesystem es específica de esta máquina. Para correr en otra máquina hay que ajustarla.

## Repositorio

- URL: https://github.com/Franco2900/campus-virtual
- Rama por defecto: `main`. Commits por unidad de trabajo (Conventional Commits). `.atl/` (herramientas locales generadas) está en `.gitignore`.

## Desarrollo spec-driven (openspec)

Los cambios se gestionan spec-driven: cada caso de uso se planifica y se implementa con un pipeline reproducible (propuesta → specs → diseño → tareas → aplicación → verificación → archivo), dejando rastro auditable en `openspec/`.

- Estructura: `openspec/changes/{cambio}/` para cambios activos, `openspec/specs/` como fuente de verdad de specs, `openspec/changes/archive/` como pista de auditoría.
- CLI: `openspec` (invocarlo en Windows como `cmd /c openspec ...` por la execution policy de PowerShell). En opencode se puede usar la vía nativa con los comandos `/opsx-*`.
- `config.yaml` contiene el contexto del proyecto, `strict_tdd` (desactivado hasta que exista un runner de tests) y las reglas por fase.
- Los casos de uso están especificados en `casos_de_uso.md`; openspec los refina por cambio.

## Roadmap

- CU-01 (Registrarse) y CU-02 (Autenticarse) implementados end-to-end (backend Flask + frontend React/Vite + tests + smoke HTTP y UI con Playwright).
- Pipeline spec-driven por CU (openspec, orquestado por `new-use-case`).
- Plugin de medición automática de tiempos.
- Integración completa del chatbot.
- Tests automatizados de frontend.

## Licencia

> PENDIENTE DE DEFINIR.

## Contacto

- Figueroa, Franco Ariel — franco2900@gmail.com — GitHub: Franco2900
