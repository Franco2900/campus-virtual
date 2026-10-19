# CU-11 (ampliación) — Eliminación del historial del chatbot

**Objetivo:** implementar A9 y A9.1 del CU-11 ampliado ("eliminar completamente el historial propio del chatbot") sobre la conversación única del usuario, dejando el borrado acotado a los datos del chat.

**Problema / por qué:** el CU-11 reescrito por el usuario agrega el objetivo de eliminar el historial, el flujo alternativo A9 (9 pasos), A9.1 (cancelación) y las reglas 14, 16 y 17. Hoy no existe ningún endpoint de borrado, ni opción en la interfaz, ni cascade: borrar la conversación dejaría mensajes huérfanos, y ninguna validación de borrado corre en el backend.

**Alcance autorizado (2026-10-19):** Bloque A completo (backend + frontend de la eliminación).
**Fuera de alcance:** Bloque B (definido como B1: historial de la conversación única, sin código), Bloque C (CU-12), la higiene de `Casos de uso.txt` (requiere OK aparte) y los documentos de cierre (tarea A-07).

**Decisiones registradas:**
- "Consultar conversaciones anteriores" = **B1**: el historial persistido de la única conversación (paso 8, A8); ya implementado, sin código nuevo.
- El borrado elimina **todas** las conversaciones del usuario con el bot (A9 paso 7).
- **Idempotente:** sin historial, la operación responde éxito (no error) y no rompe la interfaz.
- **Sin migración:** si el borrado deja cero mensajes huérfanos, no hace falta cambiar el esquema.
- La prioridad de "respuesta aprobada" y las fuentes administradas (CU-12) no se tocan en este bloque.

**Checklist:**

- [x] **A-01** Backend — `delete_history(user)` en `chat_service.py`: borra los mensajes y la conversación del usuario; devuelve resultado idempotente. Ruta: delegada (writer).
- [x] **A-02** Backend — imposibilitar mensajes huérfanos (borrado explícito ordenado o cascade a nivel ORM, sin migración) y cubrirlo con un test que verifique cero mensajes remanentes. Ruta: delegada (writer).
- [x] **A-03** Backend — endpoint `DELETE /api/chat/messages` con sesión + roles Estudiante/Profesor/Administrador, siguiendo la convención de los DELETE existentes; 401 sin sesión; idempotente. Ruta: delegada (writer).
- [x] **A-04** Backend — tests: borrado completo (mensajes + conversación), datos funcionales intactos (regla 14: cursos, tareas, entregas, inscripciones, calificaciones), aislamiento entre usuarios (regla 15), idempotencia, 401, y contexto vacío en el turno siguiente (A9 paso 9). Ruta: delegada (writer).
- [x] **A-05** Backend — el prompt del sistema orienta a la opción de borrado cuando el usuario lo pide (A4 + regla 8) y no promete ejecutarlo; cubierto con test. Ruta: delegada (writer).
- [x] **A-06** Frontend — opción "Eliminar historial" en la pantalla del chat (A9 paso 1: sección de historial o configuración), confirmación previa con el `ConfirmDialog` del design system (A9 pasos 4-6), cancelación sin efectos (A9.1), aviso de irreversibilidad, estado vacío tras borrar y método en el cliente de API. Ruta: delegada (writer).
- [x] **A-07** Verificación y cierre — pytest enfocado + suite completa, ruff check/format, prettier, build, smoke del CU-11 extendido con el borrado, evidencia UI (claro/oscuro), revisión independiente y actualización de `AGENTS.md` (tabla de API + roadmap), `decisiones.md`, `progreso.md` y la spec de openspec del chatbot. Ruta: orquestador + reviewer. **Cerrada el 2026-10-19:** todos los gates funcionales en verde y la revisión independiente APROBADA con sus 2 hallazgos Bajos corregidos y verificados; la native review (RDD) no pudo completarse en este host y quedó documentada como resultado tipado `unavailable` (ver la evidencia).

**Evidencia (2026-10-19):**
- Commits en `main`: `eb6244b` (backend — servicio + endpoint + 7 tests), `f234d08` (frontend — opción de borrado en la pantalla del chat).
- Suite completa: `..\.venv\Scripts\python.exe -m pytest -q` → **275 passed in 120.59s** (268 antes del bloque; +7 tests nuevos).
- `ruff check backend` → `All checks passed!`; `ruff format --check backend` → `48 files already formatted`.
- `npm run lint:format` → `All matched files use Prettier code style!`; `npm run build` → `built in 3.79s`.
- Smoke HTTP ampliado: `scripts\verify.py --cu cu11` → **14/14 checks** (borrado 200, historial vacío tras borrar, idempotencia, 401 sin sesión, y que el borrado no afecta a otro usuario). Tras corregir B-A1 el conteo definitivo es **15/15** (ver más abajo).
- Decisión de orfandad: borrado explícito ordenado (mensajes → conversación) en una sola transacción desde el servicio; sin migración de esquema.
- Evidencia UI Playwright en `evidencias/cu-11/` (6 capturas nuevas, claro/oscuro): `06-historial-con-mensajes-claro.png`, `07-confirmar-borrado-claro.png`, `08-historial-eliminado-claro.png`, `09-historial-con-mensajes-oscuro.png`, `10-confirmar-borrado-oscuro.png`, `11-historial-eliminado-oscuro.png`.
- Contratos verificados en la UI: cancelar no borra nada (el servidor seguía con 2 mensajes); confirmar deja `GET /api/chat/messages` → `{"conversation_id": null, "messages": []}` (sin conversación huérfana); aparece el toast "Historial eliminado"; consola del navegador sin errores.
- Limitación honesta de la sesión de evidencia: la entrega de input por ratón del navegador falló tras la navegación interna (no es defecto del producto: el handler del botón es único, `elementFromPoint` no mostró nada encima y el clic de ratón funcionó antes en la misma sesión). Los clics del flujo se ejecutaron con eventos DOM (`element.click()`) sobre los mismos botones reales, y el tema se cambió con el botón real de la app.
- Resolución de los hallazgos Bajos de la revisión independiente (2026-10-19, ver `reviews/cu-11.md`):
  - **B-A1** — `scripts/smoke_cu11.py` (commit `4980a56`): el check «el borrado no afecta a otro usuario» era tautológico (`other` nunca publicaba). Ahora `other` publica una consulta real cuando Ollama está arriba (check nuevo «otro usuario publica una consulta (201)») y, tras el DELETE del estudiante, se verifica que su historial sigue igual al tomado antes, no está vacío y no contiene mensajes del estudiante; con Ollama caído ambos checks imprimen `[SKIP]` y no se cuentan (15 checks arriba / 13 abajo, documentado en el docstring). Evidencia: `scripts\verify.py --cu cu11` → **15/15 checks PASS**.
  - **B-A2** — `frontend/src/features/chatbot/ChatPage.jsx` (commit `04e2a27`): el fallo del borrado se comunica también en la alerta de la página (`role="alert"`) con `kind: "clear"` y título propio, además del toast; «Reintentar» con ese `kind` reabre el `ConfirmDialog` (nunca borra solo) y las ramas `load`/`send` quedan intactas; sin cambios en `src/ui/`. Evidencia: `cmd /c npm run lint:format` → `All matched files use Prettier code style!`; `cmd /c npm run build` → `✓ built in 4.07s`; `ruff check backend` → `All checks passed!`.
- Documentos de cierre actualizados en el commit de docs: `AGENTS.md` (fila DELETE en la tabla de API, fila CU-12 y roadmap), `decisiones.md` (**D-043**), `progreso.md`, `openspec/specs/chatbot-assistant/spec.md` (requisito "Eliminación del historial propio" con 5 scenarios) y este archivo; `casos_de_uso.md` sincronizado desde el working tree (sin editar en este bloque).
- Revisión independiente y native review (cierre de A-07, 2026-10-19):
  - **Revisión independiente — APROBADA.** Sección "Ampliación A9/A9.1 — borrado del historial propio (2026-10-19)" al final de `reviews/cu-11.md`: 0 hallazgos Bloqueantes/Altos/Medios y 2 Bajos (B-A1: el check de aislamiento del smoke era tautológico; B-A2: el fallo del borrado no se veía en la página), ambos corregidos y verificados en los commits `4980a56` y `04e2a27`, con el bloque de resolución registrado en el mismo archivo. Limitaciones declaradas por el revisor: no puede ver imágenes, sin shell y sin `git show`.
  - **Native review (RDD activo por default) — NO ALCANZABLE en este host: resultado tipado `unavailable`, sin aprobación nativa.** Transacción `review-2b082a5930f2135f` (tier medium; candidato base-diff `b8c45176` → `8ad7770f`; 21 paths / 662 líneas; `subject_hash sha256:c4c2470a…`). El proveedor congeló el lens `review-reliability`, pero el lanzamiento de su subagente es rechazado de forma **determinista** por el tier del proveedor de OpenCode (3 intentos, mismo error; un Task de control `explore` lanzó sin problema al mismo tiempo, así que no es el prompt, ni el runtime, ni el contrato). Se registró con `gentle-ai review capture-unachievable` (`reason: reviewer_agent_provider_tier_denied`, `recorded: true`) y el proveedor cerró su transición con `action: stop` / `reason_code: unachievable_lens_slot`. Un `stop` cierra su transición y **no aprueba ni bloquea** la entrega: deja los gates en `unmanaged` y el commit/push/PR vuelve a política ordinaria del repositorio.
  - **Decisión del usuario (2026-10-19):** cerrar el CU-11 con el resultado nativo documentado como `unavailable`, sin desactivar RDD (queda activo para candidatos futuros) y sin reducir el alcance (no habría ayudado: el bloqueo es el lanzamiento del agente, no el tamaño del candidato).
  - **No corresponde** el handoff por defecto de proveedor de Gentle AI: el productor del fallo es el proveedor de modelos / runtime del cliente, que el contrato excluye explícitamente. No hay defecto de Gentle AI que reportar.
  - Abierto, pero de otros alcances (no de A-07): la higiene de `Casos de uso.txt` (requiere OK del usuario) y el Bloque C (CU-12).

**Verificación (comandos exactos):**
- `backend/`: `..\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q` y, en el gate, `..\.venv\Scripts\python.exe -m pytest -q`
- raíz: `.\.venv\Scripts\python.exe -m ruff check backend` y `.\.venv\Scripts\python.exe -m ruff format --check backend`
- `frontend/`: `cmd /c npm run lint:format` y `cmd /c npm run build`
- raíz: `.\.venv\Scripts\python.exe scripts\verify.py --cu cu11`

**Riesgos conocidos:** que el borrado deje mensajes huérfanos si se hace solo desde la ruta; que la interfaz quede con estado viejo después de borrar; que el modelo prometa ejecutar el borrado (regla 8) en lugar de orientar al usuario.

**Siguiente paso:** bloque A cerrado (A-01..A-07 `[x]`). Abierto, fuera de este bloque: la higiene de `Casos de uso.txt` (requiere OK del usuario) y el Bloque C (CU-12 — fuentes de conocimiento administrables del chatbot).
