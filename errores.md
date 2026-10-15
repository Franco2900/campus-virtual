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

## 2026-10-11 — Error de consola al anidar dos `Modal` de Bootstrap (ConfirmDialog dentro del formulario modal)

- **Fecha:** 2026-10-11.
- **Error exacto:** `TypeError: Cannot read properties of null (reading 'style')` en `Modal._hideModal` (`bootstrap/js/dist/modal.js`), disparado al cerrar el modal interno.
- **Contexto:** post-cierre de CU-04, al resolver el hallazgo 1 de la revisión (paso de confirmación al cambiar el rol). La primera implementación renderizaba `ConfirmDialog` (que envuelve un `Modal` de Bootstrap) **anidado** dentro del `Modal` de edición de `UsersPage`.
- **Causa probable (confirmada):** los modales apilados de Bootstrap 5 comparten el manejo de `document.body` y del elemento; al ocultar el modal interno mientras el externo sigue visible, `_hideModal` lee `this._element.style` sobre un elemento ya nulo. No es un defecto del código propio, sino del patrón de anidamiento.
- **Archivos involucrados:** `frontend/src/features/users/UserForm.jsx` (uso de `ConfirmDialog` anidado).
- **Diagnóstico:** reproducir el cambio de rol en la UI con Playwright y leer la consola (`browser_console_messages`): el error aparece exactamente al cerrar el diálogo interno; antes del cambio (sin anidamiento) la consola estaba limpia.
- **Solución aplicada:** reemplazar el `ConfirmDialog` anidado por un paso de confirmación **inline** dentro del mismo `Modal` (`data-testid="user-role-confirm"`, botones `user-role-confirm-cancel`/`-accept`), reutilizando `Button` y los tokens del design system. Un único modal por flujo.
- **Verificación posterior:** flujo de cambio de rol (Profesor↔Estudiante) ejecutado en Playwright → la consola reporta **0 errores desde la última navegación**; `npm run build`/Prettier OK; evidencia `evidencias/cu-04/04-cambio-rol.png` re-capturada.
- **Estado final:** Resuelto (regla: no anidar dos `Modal` de Bootstrap; usar confirmación inline dentro de un formulario modal).

## 2026-10-14 — El tool call no retorna al levantar servicios en primer plano (congelamiento aparente en CU-09)

- **Fecha:** 2026-10-14.
- **Error exacto:** sin mensaje de error; el tool call que lanzaba backend + Vite en primer plano desde el shell del agente **nunca devolvía** el control ("Saliendo..." / timeout del tool call), y al interrumpirlo morían los servicios.
- **Contexto:** evidencia de CU-09. Capturar screenshots con Playwright necesita backend (`:5000`) y Vite (`:5173`) **vivos y persistentes** entre tool calls, a diferencia del smoke, que arranca, valida y limpia en una sola corrida.
- **Causa probable (confirmada):** lanzar los servicios en primer plano mantiene **abierto el árbol de procesos y el stdio del llamador**: el proceso del agente espera el cierre de los hijos que heredaron sus handles, así que el tool call no puede resolver mientras los servicios sigan vivos. No es un cuelgue del servidor ni un defecto de Flask/Vite.
- **Archivos involucrados:** `scripts/verify.py` (falta de un modo desligado); `AGENTS.md` (comando de ejecución para evidencia UI).
- **Diagnóstico:** `python scripts/verify.py --diagnose` mostró los puertos **libres** pese a la percepción de cuelgue (los servicios no llegaban a sobrevivir a la interrupción); el working tree y los logs no mostraban progreso. Confirmado el patrón ya registrado el 2026-10-09 (percepción de congelamiento) y el 2026-10-10 (servicios que no sobreviven al reinicio).
- **Solución aplicada:** nuevo modo `scripts/verify.py --serve`: spawnea backend + Vite **desligados** del proceso del agente (Windows: `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB`, con fallback a `DETACHED_PROCESS`; POSIX: `start_new_session=True`), espera el readiness y **retorna en segundos**, dejando los pids en `scripts/.verify-pids`; `--cleanup` los detiene matando el árbol. Se documentó en `AGENTS.md` y `README.md` (D-036).
- **Verificación posterior:** `verify.py --serve` retornó en **7,7 s** (exit 0); un tool call posterior confirmó ambos servicios vivos (Vite `200`, backend `401`) con `--diagnose` en OCUPADO; `--cleanup` liberó ambos puertos y dejó `scripts/.verify-pids` vacío; las 10 capturas de `evidencias/cu-09/` se tomaron con este modo y no quedaron procesos residuales.
- **Estado final:** Resuelto (regla: nunca lanzar servicios de vida larga en primer plano desde el shell del agente; usar `--serve`).

## 2026-10-14 — Gaps de Playwright MCP con el toggle de tema (evidencia en claro/oscuro)

- **Fecha:** 2026-10-14.
- **Error exacto:** sin excepción; dos comportamientos silenciosamente engañosos: (a) el click del MCP sobre el botón de tema (`data-testid="theme-toggle"`) no llegaba a disparar el handler (`clickCount=0`), y (b) la lectura de `data-bs-theme` quedaba con un toggle de atraso, con lo que la captura podía salir en el tema **equivocado** sin que nada fallara.
- **Contexto:** captura de evidencia de CU-09 (vistas en claro y oscuro). La captura `06-detalle-estudiante-oscuro.png` salió inicialmente **idéntica en tamaño** a `05-…-claro.png`, señal de que se había capturado el tema equivocado.
- **Causa probable (confirmada):** el click del MCP no atravesó el elemento interactivo real y la actualización del atributo de tema no es observable en el mismo instante del click; ambos son detalles de sincronización del harness, no defectos de la app.
- **Archivos involucrados:** ninguno del código de la app; método de captura de evidencia.
- **Diagnóstico:** comparar el tamaño/luminancia de los PNG contra los del tema esperado; el background promedio delata el tema (claro ≈ 241, oscuro ≈ 28) y la comparación entre capturas hermanas delata la repetición.
- **Solución aplicada:** método determinista en dos pasos: (1) fijar el tema con `localStorage.setItem('campus-theme', 'dark'|'light')` y **recargar** la página, verificando `document.documentElement['data-bs-theme']` antes de capturar; (2) validar cada PNG por luminancia media de fondo con `System.Drawing` en PowerShell (medición real, no inferencia). Cuando se necesita un click, despachar `b.click()` desde `browser_evaluate` en lugar del click del MCP.
- **Verificación posterior:** las 10 capturas de `evidencias/cu-09/` pasaron la validación por píxel (claro ≈ 241, oscuro ≈ 28) y `05`/`06` y `09`/`10` se re-capturaron contra el build final.
- **Estado final:** Resuelto (regla: tema por `localStorage` + recarga verificada, y validación por píxel de cada screenshot de evidencia).

## 2026-10-14 — Prettier marca archivos CRLF que no se tocaron (artefacto de `core.autocrlf` en Windows)

- **Fecha:** 2026-10-14.
- **Error exacto:** `npm run lint:format` → `[warn] src/features/submissions/api.js`, `[warn] src/features/submissions/SubmissionForm.jsx`, `[warn] src/features/submissions/SubmissionsPage.jsx` y `Code style issues found in 3 files`, en un gate donde esos archivos **no** fueron modificados.
- **Contexto:** gate de cierre de CU-09. Los tres archivos pertenecen a CU-07 (`features/submissions/`) y no forman parte del diff de CU-09.
- **Causa probable (confirmada):** `core.autocrlf=true` (config de git de la máquina) hace que el checkout convierta LF→CRLF en el working tree, mientras el blob versionado sigue en LF. Prettier 3 usa `endOfLine: "lf"` por defecto y `frontend/.prettierrc` no lo sobreescribe, así que lee los CRLF locales como formato inválido. No es un defecto del contenido commiteado.
- **Archivos involucrados:** `frontend/src/features/submissions/{api.js,SubmissionForm.jsx,SubmissionsPage.jsx}` (no tocados); configuración de git de la máquina.
- **Diagnóstico:** `git status --porcelain` vacío para esos archivos (contenido idéntico a HEAD) + conteo de bytes: working tree con CR>0 (CRLF) vs `git show HEAD:<archivo>` con **0 CR** (LF). La distinción working tree / blob descarta la regresión. **Ojo:** `git status` puede quedar mostrando ` M` por stat cache racy aunque los bytes ya estén normalizados; la fuente de verdad es `git diff --numstat` (0 líneas = sin cambio real) más el conteo de CR.
- **Solución aplicada:** no se reformateó (un `--write` cambiaría los finales de línea y ensuciaría el diff con ruido ajeno al CU). Se verificó el contenido versionado y se reportó el `warn` como preexistente del entorno. Los archivos creados/modificados en CU-09 se escribieron en LF y pasan el check.
- **Verificación posterior:** `prettier --check .` no marca ningún archivo de `features/grades/` ni de los modificados en CU-09; el conteo de CR confirma LF en los archivos nuevos.
- **Estado:** Abierto (limitación del entorno Windows; no requiere cambio de código). Mitigación posible si molesta: `.gitattributes` con `* text=auto eol=lf`, que tiene precedencia sobre `core.autocrlf`.
