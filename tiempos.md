# Registro de tiempos

Medición del tiempo invertido en el desarrollo del Campus Virtual (TP Integrador).

- Convención de hora: local del sistema, formato ISO 8601 (`YYYY-MM-DDTHH:MM:SS`).
- Duración: diferencia entre fin e inicio, formato `HH:MM:SS`.
- Actor: `Humano`, `Agente` o `Humano+Agente` (trabajo conjunto en la misma unidad).

## Cómo se registra

1. Al iniciar una unidad de trabajo (tarea, caso de uso, decisión, verificación) se captura la marca de inicio. Portátil: Windows PowerShell `Get-Date -Format "yyyy-MM-ddTHH:mm:ss"`; Linux/macOS `date +"%Y-%m-%dT%H:%M:%S"`.
2. Al terminar la unidad se captura la marca de fin.
3. Se agrega una fila al registro y se actualizan los totales.

### Límite conocido de la medición

El tiempo del agente se mide por **límites de unidad en tiempo real (wall-clock)**. No separa con precisión quirúrgica "pensar" de "escribir código". Para obtener duraciones por acción/tool se requiere instrumentación mediante un plugin de opencode (mejora futura, ver `progreso.md`).

## Categorías

| Código | Categoría |
|--------|-----------|
| DEC | Decisión / análisis |
| DIS | Diseño |
| IMP | Implementación de código |
| TST | Testing / verificación |
| DOC | Documentación |
| CFG | Configuración / setup |
| REV | Revisión |

## Registro

| ID | Inicio | Fin | Duración | Cat. | CU | Actor | Descripción |
|----|--------|-----|----------|------|----|-------|-------------|
| T-001 | 2026-10-09T11:45:05 | 2026-10-09T11:55:13 | 00:10:08 | DEC | - | Humano+Agente | Análisis de casos de uso, consignas y plantilla; propuesta de MCPs, skills, arquitectura y plan |
| T-002 | 2026-10-09T11:55:13 | 2026-10-09T11:56:41 | 00:01:28 | DOC | - | Agente | Fase 1: creación de documentación base del proyecto |
| T-003 | 2026-10-09T11:56:41 | 2026-10-09T12:02:46 | 00:06:05 | CFG | - | Humano+Agente | Fase 2: `opencode.json` (MCP filesystem + permisos); verificación de `npx`/execution policy y arranque del server |
| T-004 | 2026-10-09T12:02:46 | 2026-10-09T12:11:08 | 00:08:22 | CFG | - | Agente | Fase 3+4: subagentes (backend, frontend, database, tester, reviewer) y skills (track-time, new-use-case, create-crud, create-migration, run-verification); registro `.atl/skill-registry.md` y actualización de docs |
| T-005 | 2026-10-09T12:19:05 | 2026-10-09T12:33:15 | 00:14:10 | CFG | - | Humano+Agente | Fase 5: verificación de MCPs/subagentes/skills, `git init`, `.gitignore` (incl. `.atl/`), 4 commits por work-unit, `gh auth login`, repo público `campus-virtual`, push y cierre documental |
| T-006 | 2026-10-09T12:43:52 | 2026-10-09T12:50:19 | 00:06:27 | CFG | - | Agente | Fase 6, paso cero: `openspec init` v1.13.2 (--tools opencode --language es), `openspec/config.yaml` enriquecido (strict_tdd: false), registro de 6 skills `openspec-*` y 6 comandos `/opsx-*`, docs (D-005 Superada, D-009) |
| T-007 | 2026-10-09T13:06:13 | 2026-10-09T13:08:03 | 00:01:50 | DIS | CU-01 | Agente | CU-01 (planning): cambio openspec `add-user-registration` — proposal, specs/user-auth (delta), design, tasks; validado con `openspec validate --strict` |
| T-008 | 2026-10-09T13:10:25 | 2026-10-09T13:27:56 | 00:17:31 | IMP | CU-01 | Agente | CU-01 (apply): subagentes `backend` (scaffolding, modelo User, servicio, endpoint, 21 tests) y `frontend` (Vite 7 + React 19, cliente API, RegisterForm); mensajes de error a español; smoke end-to-end (201/409 vía proxy); docs (AGENTS, README, decisiones D-010, progreso, prompts_log, errores) |
| T-009 | 2026-10-09T13:27:56 | 2026-10-09T13:34:24 | 00:06:28 | REV | CU-01 | Agente | CU-01 (cierre): verificación final (pytest 21 passed, build, smoke), revisión inline del checklist `reviewer` (subagente falló por tier del proveedor; aceptada por el usuario), sync de specs y archive openspec (`2026-10-09-add-user-registration`), docs de cierre |
| T-010 | 2026-10-09T13:46:34 | 2026-10-09T13:51:02 | 00:04:28 | DIS | CU-02 | Agente | CU-02 (planning): cambio openspec `add-user-auth` — proposal, delta specs/user-auth (5 requirements ADDED), design (D-A..D-G), tasks (7 grupos, 16 tareas); validado con `openspec validate add-user-auth --strict` |
| T-011 | 2026-10-10T08:19:00 | 2026-10-10T08:31:00 | 00:12:00 | IMP | CU-02 | Humano+Agente | CU-02 (cierre, smoke): diagnóstico de sesiones/`reviewer`; `scripts/verify_cu02.py` (wrapper portable: pre-condición de puertos, readiness, smoke contra el proxy, cleanup del árbol — mata el `node vite` huérfano); install del browser Chrome for Testing; smoke HTTP `10/10 PASS`; smoke de UI con Playwright (registro→login→header rol→logout→error del backend renderizado) con 4 screenshots en `evidencias/cu-02/`; cleanup garantizado |
| T-012 | 2026-10-10T08:31:00 | 2026-10-10T08:35:00 | 00:04:00 | DOC | CU-02 | Agente | CU-02 (cierre, docs): tasks 6.1-6.2 `[x]`; AGENTS (tabla API 4 endpoints, smoke CU-02, MCP playwright, roadmap), README (API, testing, MCP, características, roadmap), `decisiones.md` D-011, `errores.md` (huérfanos + cierre del punto de freeze), `progreso.md`, `prompts_log.md` |
| T-013 | 2026-10-10T08:35:00 | 2026-10-10T08:38:40 | 00:03:40 | REV | CU-02 | Agente | CU-02 (cierre, revisión y archive): reintento del subagente `reviewer` (falló por tier, como en CU-01) → revisión inline del checklist sin bloqueantes (APROBADO); `openspec archive add-user-auth --yes` → `2026-10-10-add-user-auth` (specs sincronizadas, +4 requirements); `openspec validate --specs --strict` → 1 passed; commits por unidad (6)

| T-014 | 2026-10-10T10:26:49 | 2026-10-10T10:39:00 | 00:12:11 | IMP | CU-03 | Humano+Agente | CU-03 (propose + apply): cambio `add-course-management` (proposal/specs/design/tasks); backend (modelo `Course`, `course_service` con validaciones, blueprint `courses` con `@login_required`+`@require_roles`, `seed_admin.py` con env obligatorio e idempotente); frontend (ruteo con `react-router-dom`, `features/courses` API/`CoursesPage`/`CourseForm`); tests (23 nuevos); `scripts/verify.py` con base temporal aislada + seed |
| T-015 | 2026-10-10T10:39:00 | 2026-10-10T10:42:34 | 00:03:34 | TST | CU-03 | Agente | CU-03 (verify): `pytest` 55 passed; `ruff check`/`format` y Prettier OK; `npm run build` OK; smoke end-to-end `Smoke CU-03: 13/13 PASS` (y regresión CU-02 10/10 PASS); evidencia UI Playwright (7 screenshots en `evidencias/cu-03/`); bug detectado y corregido (registro no inicia sesión → navegar a `/login`, D-018) |

## Totales

| Categoría | Duración acumulada |
|-----------|--------------------|
| DEC | 00:10:08 |
| DIS | 00:06:18 |
| IMP | 00:41:42 |
| TST | 00:03:34 |
| DOC | 00:05:28 |
| CFG | 00:35:04 |
| REV | 00:10:08 |
| **Total** | **01:52:22** |
