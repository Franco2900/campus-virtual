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

## Totales

| Categoría | Duración acumulada |
|-----------|--------------------|
| DEC | 00:10:08 |
| DIS | 00:01:50 |
| IMP | 00:17:31 |
| TST | 00:00:00 |
| DOC | 00:01:28 |
| CFG | 00:35:04 |
| REV | 00:06:28 |
| **Total** | **01:12:29** |
