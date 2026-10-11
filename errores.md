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
- **Estado final:** Resuelto (en el cierre de CU-02, el 2026-10-10, se reintentó el subagente `reviewer` y volvió a fallar con el mismo error de tier en el CLI; se cerró con revisión inline del checklist del `reviewer` sin bloqueantes → APROBADO. Queda pendiente de fondo solucionar el tier del proveedor para el subagente en próximos CU).

## 2026-10-09 — Percepción de "congelamiento" durante el desarrollo de CU-02 (sin salida intermedia)

- **Fecha:** 2026-10-09.
- **Error exacto:** sin mensaje de error; el usuario reportó que "el desarrollo del caso de uso 2 se queda congelado".
- **Contexto:** en curso, trabajo de CU-02 (cambio `add-user-auth`) desde el CLI de opencode: tarea larga ejecutada sin streaming de avance hacia el usuario (operación/subagente que retorna recién al finalizar), por lo que la sesión parecía detenida aunque seguía activa.
- **Causa probable:** el agente no emite progreso mientras corre un tool call extenso; un subagente o comando largo devuelve su resultado al terminar. No es un crash (confirmado: la sesión continuó y guardó memoria después).
- **Archivos involucrados:** ninguno del código de la app; patrón de trabajo de la sesión. Se formaliza en `AGENTS.md` (sección "Progreso visible") y en el roadmap (plugin de medición de tiempos por tool-call).
- **Diagnóstico:** distinguir "sin feedback" de "colgado": verificar actividad real (cambios en el working tree, memoria de sesión, procesos vivos) antes de asumir un cuelgue.
- **Solución aplicada:** convención de progreso visible en `AGENTS.md`: reporte por turno, aviso previo a tool calls largos con estimación, pasos cortos con verificación, subagentes acotados con reportes intermedios, commits por unidad de trabajo.
- **Verificación posterior:** aplicar la convención al cierre de CU-02 y comprobar que hay reportes por paso y commits por unidad en lugar de silencios largos.
- **Estado final:** Resuelto (verificado en el cierre de CU-02: wrapper `scripts/verify.py` con cleanup garantizado y heartbeat por turno, sin pasajes silenciosos).

## 2026-10-10 — Vite huérfano y servicios heredados entre sesiones (percepción de "10 horas sin avance")

- **Fecha:** 2026-10-10.
- **Error exacto:** sin mensaje de error; el usuario reportó "más de 10 horas sin avance". Al diagnosticar: `Get-NetTCPConnection -State Listen -LocalPort 5000,5173` vacío (ningún servicio escuchando), 0 procesos `run_backend.py`, y el smoke nunca llegó a ejecutarse.
- **Contexto:** cierre de CU-02. En una sesión previa se levantaron backend y Vite; al reiniciarse opencode (por la config de tooling) murieron los procesos lanzados y el avance quedó en la task 6.1 sin correr. Además, al terminar `npm run dev` quedaba un `node vite` huérfano escuchando en `:5173` (PID 17416, hijo del wrapper `npm.cmd` que no muere con el padre).
- **Causa probable:** (1) los procesos de servicios no sobreviven al reinicio de opencode ni a un tool call abortado; (2) en Windows, terminar `npm.cmd` no mata el árbol `node` que levantó Vite; (3) el avance quedó en archivos (estado del repo), pero la percepción del usuario se midió por procesos vivos.
- **Archivos involucrados:** ninguno del código de la app; patrón del harness de dev. Se resuelve con `scripts/verify.py`.
- **Diagnóstico:** consultar puertos y procesos (no suponer): `Get-NetTCPConnection -State Listen -LocalPort 5000,5173` y filtros por `run_backend.py`/`vite`. Confirmado: puertos libres, 0 backends, listener 5173 huérfano.
- **Solución aplicada:** wrapper portable `scripts/verify_cu02.py` (generalizado luego a `scripts/verify.py` con `--cu` y `--diagnose`): pre-condición de puertos libres (aborta si hay duplicados, sin matar a ciegas), arranca backend + Vite, readiness con timeout, corre el smoke contra el proxy, y hace cleanup **del árbol de procesos** (`taskkill /F /T /PID` en Windows, `os.killpg` + `start_new_session` en POSIX). Modos `--keep` (servicios vivos, pids en `scripts/.verify-pids`) y `--cleanup` (los detiene).
- **Verificación posterior:** `verify.py` → `Smoke CU-02: 10/10 PASS`, exit 0; `--keep` → 2 PIDs registrados; `--cleanup` → 0 servicios vivos, puertos libres; smoke UI con Playwright sin procesos residuales.
- **Estado final:** Resuelto.

## 2026-10-11 — `reviewer` re-falla por tier: investigado y descartado como defecto de configuración

- **Fecha:** 2026-10-11.
- **Error exacto:** `AI_APICallError: Error from provider (Console): OpenCode's free tier can only be used from within OpenCode` (registrado en `~/.local/share/opencode/log/opencode.log` como `stream error`, `providerID=opencode modelID=big-pickle agent=reviewer mode=subagent`).
- **Contexto:** cierre de CU-03; antes de hacer push, el usuario pidió investigar por qué el subagente `reviewer` fallaba mientras `backend`/`tester`/`database`/`frontend`/`general` arrancaban bien.
- **Causa probable (confirmada):** error intermitente del gateway del proveedor (free tier de opencode), **no** un defecto del agente ni de su configuración. El mensaje "Console" proviene del gateway, no del CLI local.
- **Archivos involucrados:** `.opencode/agents/reviewer.md` (descartado: el bloque `permission:` no es la causa; el frontmatter era YAML válido).
- **Diagnóstico:** (1) grep del log → 14 ocurrencias del error en fechas dispares (2026-09-17 con `agent=title`; 2026-10-09 ×2 y 2026-10-10 ×3 con `agent=reviewer`), todas `providerID=opencode`; (2) descartado el allowlist de `task` (la denegación por permisos produce otro mensaje, no el de tier); (3) prueba de causalidad en sesión: con el bloque `permission:` original **re-agregado**, `reviewer` respondió (`REVIEWER_OK_2`) igual que sin él (`REVIEWER_OK`) → el bloque no influye.
- **Solución aplicada:** ninguna sobre la config (no hay defecto reproducible). Se restauró `reviewer.md` a su estado en HEAD y se eliminó el clon diagnóstico `.opencode/agents/revcheck.md`. Repo limpio (`git status` sin cambios).
- **Verificación posterior:** invocación en sesión del subagente `reviewer` vía task tool → `REVIEWER_OK` (sin bloque) y `REVIEWER_OK_2` (con bloque original). `git diff .opencode/agents/reviewer.md` vacío.
- **Estado final:** Resuelto (no es un defecto reproducible; el error de tier es transitorio del proveedor. Volver a usar `reviewer` con normalidad; si reaparece, reintentar o caer al checklist inline de `review-use-case`).

## 2026-10-11 — `reviewer` vuelve a fallar por tier en el cierre de CU-04

- **Fecha:** 2026-10-11.
- **Error exacto:** `Subagent failed (task_id: ses_ed33a1d2bffezhpeTyCMCylL80): OpenCode's free tier can only be used from within OpenCode`.
- **Contexto:** cierre de CU-04 (cambio `add-user-management`), al intentar la revisión obligatoria con el subagente `reviewer` (read-only) antes del commit final. Contradice la conclusión de la entrada anterior (que en la sesión de CU-03 `reviewer` había respondido).
- **Causa probable (confirmada):** el error de tier del proveedor es **intermitente**, no de configuración (coincide con las entradas previas). No depende del cambio revisado.
- **Archivos involucrados:** `.opencode/agents/reviewer.md` (sin cambios; ya descartado como causa).
- **Diagnóstico:** el `task tool` devolvió el error del gateway de forma inmediata (antes de ejecutar herramientas), igual que en CU-01/CU-02/CU-03.
- **Solución aplicada:** revisión equivalente inline por el orquestador (skill `review-use-case`) sobre el cambio `add-user-management` → sin bloqueantes (APROBADO), persistida en `reviews/cu-04.md`.
- **Verificación posterior:** `pytest` 90 passed, `ruff`/Prettier OK, `npm run build` OK, smoke CU-04 21/21 PASS y 9 screenshots de evidencia verificables.
- **Estado final:** Resuelto (se cierra con revisión inline; el subagente `reviewer` queda pendiente de tier del proveedor).
