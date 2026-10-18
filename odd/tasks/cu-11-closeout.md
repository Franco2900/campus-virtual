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
- [x] T3 — `progreso.md`: CU-11 **Completado**; `AGENTS.md` roadmap actualizado (lista de cerradas incluye CU-11, resumen de cierre con archivo y nota de `reviewer` con CU-11).
- [x] T4 — Reconciliación 51/51 de tasks (`a8de937`), sync a spec main (12 requisitos, `validate --specs --strict` 11/11 ✓) y archive `openspec/changes/archive/2026-10-17-add-chatbot-assistant` (`7179d70`).
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
- [x] T1 (5be3536) … [x] T2 (c6edd07) … [x] T3 … [x] T4 (a8de937, 7179d70) …

## Siguiente paso
Cierre completo: T1–T4 terminados (evidencia `5be3536`, revisión `c6edd07`,
reconcile `a8de937`, archive `7179d70` y docs de cierre). Sin pendientes;
próximo hito: mantenimiento nuevo (deuda B-01/B-04) o cerrar sesión.
