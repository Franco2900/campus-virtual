# Bitácora de errores

Registro de errores relevantes del proyecto. Evita repetir diagnósticos.

Formato de cada entrada:

- **Fecha:** `YYYY-MM-DD`.
- **Error exacto:** mensaje completo (sin recortar).
- **Contexto:** qué se estaba haciendo y con qué herramienta/versión.
- **Causa probable:** hipótesis (diferenciar confirmada vs. probable).
- **Archivos involucrados:** rutas.
- **Diagnóstico:** pasos realizados (reproducibles).
- **Solución aplicada:** cambio mínimo.
- **Verificación posterior:** cómo se confirmó la corrección.
- **Estado final:** Resuelto / Pendiente.

---

> Sin errores registrados hasta CU-01; primera entrada durante el smoke.

---

## 2026-10-09 — Conexión cerrada en el primer request proxeado por Vite

- **Fecha:** 2026-10-09.
- **Error exacto:** `Se ha terminado la conexión: Una conexión que se esperaba que se mantuviera activa fue cerrada por el servidor.` (Invoke-WebRequest contra `http://localhost:5173/api/auth/register`).
- **Contexto:** smoke end-to-end del cambio `add-user-registration` (task 6.2): backend Flask en `:5000` y Vite dev en `:5173` arrancados casi en paralelo; primer `POST` vía proxy.
- **Causa probable:** race de arranque — el primer request entró al proxy antes de que el backend terminara de bindear (el segundo request con el mismo payload respondió 201).
- **Archivos involucrados:** `frontend/vite.config.js` (proxy), `backend/app.py`.
- **Diagnóstico:** repetir el smoke esperando `readiness` del backend (poll a `:5000`) antes de probar el proxy; entonces el primer request devuelve 201 y el duplicado 409.
- **Solución aplicada:** en el smoke, poll de readiness de backend y de Vite antes de emitir requests; el bug no es de la app.
- **Verificación posterior:** smoke re-ejecutado con readiness: `PROXY FIRST: HTTP 201` + `PROXY SECOND: HTTP 409`.
- **Estado final:** Resuelto (gotcha del harness de smoke: levantar el backend antes que el frontend).

## 2026-10-09 — Subagente `reviewer` no arranca (error de tier del proveedor)

- **Fecha:** 2026-10-09.
- **Error exacto:** `Subagent failed (task_id: ses_edda...): OpenCode's free tier can only be used from within OpenCode`.
- **Contexto:** antes de marcar CU-01 como Completo, al delegar la revisión obligatoria al subagente `reviewer` (read-only) del proyecto desde el CLI de opencode durante el apply del cambio `add-user-registration`. Dos intentos consecutivos fallaron igual; el subagente `backend` y `frontend` funcionaron en la misma sesión.
- **Causa probable:** error del proveedor de modelos al resolver el agente `reviewer` (tier/ratelimit), no un problema del código del agente ni del cambio.
- **Archivos involucrados:** `.opencode/agents/reviewer.md` (sin `model` explícito; usa el modelo por defecto).
- **Diagnóstico:** la falla ocurre al lanzar (antes de ejecutar herramientas), por lo que no depende de permisos del agente; se descartó problema de permisos o syntaxis del frontmatter.
- **Solución aplicada:** revisión equivalente realizada inline por el orquestador contra el checklist del `reviewer` (CU, reglas de negocio, arquitectura, seguridad, portabilidad, docs, escenarios de la spec) → sin bloqueantes (APROBADO). Pendiente de confirmar con el usuario si se re-ejecuta el `reviewer` antes de archivar.
- **Verificación posterior:** corrección de los hallazgos revisada contra `backend/tests/test_register.py` (21 passed) y compilación del frontend.
- **Estado final:** Pendiente (decisión del usuario: reintentar el subagente o aceptar la revisión inline).
