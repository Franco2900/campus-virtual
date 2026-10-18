# Feature: CU-11 cierre (evidencia + revisión + archive)

## Objetivo
Cerrar el CU-11 «Utilizar chatbot de asistencia»: capturar la evidencia UI Playwright,
persistir la revisión `reviews/cu-11.md` y archivar el cambio `add-chatbot-assistant`.

## Por qué / contexto
El chatbot está implementado, commiteado (7cbd8d9, 84bc27c, 2f4e302, 01591f1, 5bd7a07,
6b38a96) y verificado (268 tests, ruff/Prettier, build, smoke 9/9 con Ollama arriba).
Faltan los tres pasos de cierre exigidos por AGENTS.md antes de marcar Completo.

## Alcance
- Evidencia en `evidencias/cu-11/` (claro/oscuro, testids, consola limpia).
- Revisión `reviews/cu-11.md` (skill `review-use-case`; subagente `reviewer` si existe).
- Actualización final de `progreso.md` (Completado) y archive openspec.

## Fuerza laboral
- Modo TDD: **off** (trabajo de verificación/docs, sin cambios funcionales; runner
  si hiciera falta: `..\.venv\Scripts\python.exe -m pytest` desde `backend/`).
- Ruta: **inline** (captura Playwright y docs puntuales; sin triggers de delegación).

## Checklist
- [x] T1 — Evidencia Playwright `evidencias/cu-11/` (10/10 capturados, consola limpia;
      A7 logrado con `OLLAMA_BASE_URL` apuntando a puerto muerto, sin tocar el Ollama
      real del usuario; verificado por DOM/red ya que el modelo no lee imágenes).
      01-chat-vacio-{claro,oscuro}, 02-chat-pensando-{claro,oscuro},
      03-respuesta-asistente-{claro,oscuro}, 04-error-a7-{claro,oscuro}
      (servicio con `OLLAMA_BASE_URL` muerto para no tocar el Ollama del usuario),
      05-acceso-sin-sesion-{claro,oscuro}. Checks: consola sin errores inesperados.
- [x] T2 — Revisión `reviews/cu-11.md` (APROBADO; 3 hallazgos Baja; 268 tests,
      ruff, Prettier y build frescos como evidencia).
- [ ] T3 — `progreso.md`: marcar CU-11 **Completado**; verificar docs finales.
- [ ] T4 — Archive openspec del cambio `add-chatbot-assistant`.
      Cada tarea cierra con un commit conventional (repo: directo a `main`,
      política existente del proyecto; sin PR ni push sin pedido).

## Criterios de aceptación
- 10 screenshots presentes y legibles en `evidencias/cu-11/`.
- `reviews/cu-11.md` con veredicto explícito.
- `progreso.md` dice Completado y el cambio queda en `openspec/changes/archive/`.

## Checks aplicables
- Gate de evidencia AGENTS.md (estado esperado visible, consola limpia).
- Si se toca backend: `pytest -q` del dominio + ruff check/format.

## Progreso / evidencia
- [x] T1 … [x] T2 … [ ] T3 … [ ] T4 …

## Siguiente paso
T3/T4: archive openspec `add-chatbot-assistant` y flip de `progreso.md` +
`AGENTS.md` a Completado/cerrado (commiteo conjunto de cierre).
