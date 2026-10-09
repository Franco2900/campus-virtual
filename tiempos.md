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

## Totales

| Categoría | Duración acumulada |
|-----------|--------------------|
| DEC | 00:10:08 |
| DIS | 00:00:00 |
| IMP | 00:00:00 |
| TST | 00:00:00 |
| DOC | 00:01:28 |
| CFG | 00:28:37 |
| REV | 00:00:00 |
| **Total** | **00:40:13** |
