# Feature: mantenimiento — fechas naive-UTC + hallazgos Baja del CU-11

## Objetivo
Cerrar la deuda conocida y los hallazgos Baja pendientes: unificar el tratamiento de fechas
naive-UTC en el frontend (B-01 de `reviews/cu-09.md`), alinear el selector de tareas de la
corrección con `/grades` (B-04 de `reviews/cu-10.md`), corregir los 3 hallazgos Baja del CU-11
y reparar la disponibilidad del subagente `reviewer`.

## Problema / por qué
- **B-01 (fechas):** el backend persiste y devuelve fechas naive en UTC; el cliente las parsea
  con `new Date(...)` como hora local → para usuarios en UTC-3 la fecha límite se muestra ~3 h
  corrida respecto del valor con el que el servidor evalúa el vencimiento. El desarrollo (UTC)
  lo enmascara. Afecta `tasks`, `submissions` y `grades`.
- **B-04 (filtro):** la matriz de `/grades` solo considera tareas activas (backend,
  `grade_service._active_tasks`), pero el selector de `GradingPage` lista también las inactivas.
- **CU-11 Baja:** docs con nombres de tabla en plural, system prompt sin la regla 14 codificada,
  imports de modelos en `app.py` por side-effect.
- **`reviewer`:** la allowlist `permission.task` del orquestador (config global) deniega con
  `"*": "deny"` a todos los agentes del proyecto → la instrucción de AGENTS.md de usar los
  subagentes del proyecto es inejecutable en este runtime.

## Alcance
- [x] M-01 — Crear `frontend/src/api/dates.js` (`parseServerDate`, `formatDueDate`,
      `isoToLocalInput`) y consumirlo en `features/grades/format.js`,
      `features/tasks/TasksPage.jsx`, `features/submissions/SubmissionsPage.jsx` y
      `features/tasks/TaskForm.jsx` (no existe `formatSubmissionDate`).
- [x] M-02 — `features/grading/GradingPage.jsx`: filtrar tareas inactivas del selector y quitar
      la etiqueta "— inactiva".
- [x] M-03 — Docs: `conversations`/`messages` → `conversation`/`message` en `decisiones.md`
      (D-040), `AGENTS.md:49` y `progreso.md:68`.
- [x] M-04 — `backend/services/chat_service.py`: codificar la regla 14 en el system prompt +
      assert en `backend/tests/test_chat.py`.
- [x] M-05 — `backend/app.py`: agregar `conversation`/`message` al bloque de imports de modelos.
- [x] M-06 — Allowlist de subagentes del proyecto en la config global del orquestador y causa
      raíz registrada en `decisiones.md`.
- [x] M-07 — Registro: `decisiones.md` (D-041 fechas, D-042 subagentes) y `progreso.md` (entrada
      de mantenimiento).

## Fuera de alcance
- Refactor del formato de fechas en el backend (no se toca el contrato del API).
- Infra de tests de frontend (no existe runner; no se introduce uno).
- El evento de guardado del formulario de tareas (`TaskForm` → `toISOString()` ya envía UTC
  correcto; no se toca).

## Restricciones
- No tocar el Ollama del usuario (puerto 11434).
- Sin dependencias nuevas.
- Frontend sin runner de tests: verificación = `prettier --check`, `vite build` y verificación
  ejecutada del helper con `node` (ESM, `TZ=America/Argentina/Buenos_Aires`).
- Backend: `pytest` del dominio + `ruff`.

## Criterios de aceptación
- El helper trata las fechas naive del servidor como UTC y las muestra en hora local
  (verificado con `node` bajo `TZ=America/Argentina/Buenos_Aires`).
- `GradingPage` no ofrece tareas inactivas; la corrección y `/grades` coinciden en criterio.
- `pytest` del chat en verde con el assert nuevo; suite completa en verde al cierre.
- `ruff check`/`ruff format --check`/`prettier --check`/`vite build` en verde.
- Documentación sin plurales incorrectos y con D-041/D-042 registradas.

## Verificación
- Backend: `..\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q` (desde `backend/`),
  luego suite completa.
- Lint: `.\.venv\Scripts\python.exe -m ruff check backend` y `-m ruff format --check backend`.
- Frontend: `cmd /c npm run lint:format` y `cmd /c npm run build` (desde `frontend/`).
- Helper: `node` ESM con `TZ=America/Argentina/Buenos_Aires` (casos: naive, con `Z`, inválido,
  vacío, `isoToLocalInput`).

## Progreso / evidencia
- [x] **M-01** — `frontend/src/api/dates.js` creado (`parseServerDate`/`formatDueDate`/`isoToLocalInput`,
      regex de zona `/(?:Z|[+-]\d{2}:?\d{2})$/`); consumido por `features/grades/format.js` (import +
      re-export), `features/tasks/TasksPage.jsx`, `features/submissions/SubmissionsPage.jsx` y
      `features/tasks/TaskForm.jsx` (copias locales borradas; `:35` de guardado intacto).
      Evidencia: script `node` ESM bajo `TZ=America/Argentina/Buenos_Aires` (naive → 12:30 local,
      con `Z`, inválido, vacío, `isoToLocalInput`), 8/8 OK. Commit `a1fae15`.
- [x] **M-02** — `GradingPage.jsx`: `setTasks((data ?? []).filter((task) => task.active))` y `<option>`
      sin la etiqueta "— inactiva". Commit `e2c6e92`.
- [x] **M-03** — `decisiones.md` (D-040), `AGENTS.md:49` y `progreso.md:68` en singular; verificado que
      ya no quedan plurales incorrectos. Commit `docs`.
- [x] **M-04** — regla 14 en `chat_service._build_system_prompt` ("Priorizá los datos actuales y
      verificados…") + `assert "datos actuales" in prompt`. `pytest tests/test_chat.py -q` → 27 passed.
      Commit `86b9817`.
- [x] **M-05** — `app.py`: `conversation` y `message` agregados en orden alfabético al bloque
      `from models import (  # noqa: F401`. Commit `77fa54f`.
- [x] **M-06** — allowlist `permission.task` del orquestador ampliada con `backend`, `database`,
      `frontend`, `reviewer`, `tester` en `C:\Users\Administrador\.config\opencode\opencode.jsonc`
      (fuera del repo, no se commitea); causa raíz en D-042. Verificación pendiente de reiniciar OpenCode.
- [x] **M-07** — `decisiones.md` D-041/D-042; `progreso.md` (ítems 2-4 reescritos como resueltos +
      mantenimiento); `AGENTS.md` (deuda de B-01/B-04 marcada resuelta).
- **Gate de cierre (2026-10-19):** suite completa `..\.venv\Scripts\python.exe -m pytest -q` →
      **268 passed in 196.70s**; `ruff check backend` → All checks passed; `ruff format --check backend`
      → 48 files already formatted; `cmd /c npm run lint:format` → OK; `cmd /c npm run build` → ✓ built;
      grep de `new Date(` en `frontend/src` → solo el helper y el guardado UTC de `TaskForm:35`.

## Siguiente paso
Mantenimiento cerrado el 2026-10-19 (commits `a1fae15`, `e2c6e92`, `86b9817`, `77fa54f` y el de docs).
Pendiente de verificación externa: reiniciar OpenCode y comprobar que el subagente `reviewer` ya es
invocable (D-042). Retomar con el usuario el alcance del trabajo nuevo sobre el chatbot.
