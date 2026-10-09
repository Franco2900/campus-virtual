# Registro de prompts

Auditoría de los prompts utilizados con agentes de IA. Permite reproducir cómo se llegó a una implementación.

Formato de cada entrada:

- **Fecha:** `YYYY-MM-DD HH:MM`.
- **Contexto / CU / tarea.**
- **Prompt utilizado.**
- **Resumen de la respuesta.**
- **Archivos modificados.**
- **Resultado.**
- **Estado:** Pendiente / En progreso / Completado.
- **Verificaciones realizadas.**

---

## 2026-10-09 11:45 — Inicialización del proyecto

- **Contexto / tarea:** Fase 0-1. Definición del entorno de trabajo con IA (MCPs, skills, plan).
- **Prompt utilizado (resumen):** "Vamos a hacer un proyecto de un campus virtual... recomienda qué MCP y skills implementar... usar MCP de Memoria, Filesystem/Terminal y Documentación... medir tiempos en un archivo aparte... proponer un plan."
- **Resumen de la respuesta:** análisis de `Casos de uso.txt`, `Consignas TP.txt` y la plantilla; recomendación de MCPs (engram, context7, filesystem) y skills; diseño de `tiempos.md`; plan por fases; arquitectura de backend.
- **Archivos modificados:** ninguno (modo plan).
- **Resultado:** plan aprobado; decisiones D-001 a D-005.
- **Estado:** Completado.
- **Verificaciones:** no aplica.

## 2026-10-09 11:55 — Fase 1: documentación base

- **Contexto / tarea:** Fase 1. Creación de la documentación base del proyecto.
- **Prompt utilizado:** "Empezá con la fase 1."
- **Resumen de la respuesta:** se crean `tiempos.md`, `casos_de_uso.md`, `AGENTS.md`, `README.md`, `decisiones.md`, `errores.md`, `progreso.md` y `prompts_log.md`.
- **Archivos modificados:** ver lista anterior.
- **Resultado:** documentación base creada con los PENDIENTE DE DEFINIR marcados.
- **Estado:** Completado.
- **Verificaciones:** revisión de presencia y contenido de los archivos creados.

## 2026-10-09 12:02 — Fase 2: configuración de proyecto

- **Contexto / tarea:** Fase 2. `opencode.json` de proyecto con MCP de filesystem y permisos.
- **Prompt utilizado:** "Arranca con la fase 2."
- **Resumen de la respuesta:** se creó `opencode.json` con el MCP local `filesystem` (`cmd /c npx -y @modelcontextprotocol/server-filesystem "<ruta>"`) y un bloque de permisos. Se verificó `npx` (falla por execution policy en PowerShell; un spawn directo da `ENOENT`, por eso se usa `cmd /c`), la existencia del paquete (v2026.8.31) y el arranque real del server (`Secure MCP Filesystem Server running on stdio`). Se documentaron los MCP en el README y AGENTS.md.
- **Archivos modificados:** `opencode.json` (nuevo), `README.md`, `AGENTS.md`, `decisiones.md` (D-006), `progreso.md`, `tiempos.md`, `prompts_log.md`.
- **Resultado:** configuración de proyecto lista; requiere reinicio de opencode.
- **Estado:** Completado.
- **Verificaciones:** JSON parseado con Node; arranque del server MCP probado con `Start-Process`.

## 2026-10-09 12:11 — Fase 3 + 4: subagentes y skills

- **Contexto / tarea:** Fase 3 y 4. Subagentes especializados y skills reutilizables.
- **Prompt utilizado:** "Antes de crear las skills y subagentes, no te olvides que el proyecto debe andar en cualquier sistema operativo y que siempre me tenes que recomendar skills o subagentes cuando creas que haga falta."
- **Resumen de la respuesta:** se crearon 5 subagentes (backend, frontend, database, tester, reviewer read-only) y 5 skills (track-time, new-use-case, create-crud, create-migration, run-verification) siguiendo el style-guide LLM-first. Se regeneró `.atl/skill-registry.md` y se agregó la sección `Portabilidad` a AGENTS.md, aclarando que `opencode.json` es tooling local de la máquina.
- **Archivos modificados:** `.opencode/agents/*.md`, `.opencode/skills/*/SKILL.md`, `.atl/skill-registry.md`, `AGENTS.md`, `decisiones.md` (D-007), `progreso.md`, `tiempos.md`, `prompts_log.md`.
- **Resultado:** entorno de agentes/skills listo.
- **Estado:** Completado.
- **Verificaciones:** style-guide aplicado; registro regenerado y persistido en memoria.

## 2026-10-09 12:19 — Fase 5: git + GitHub

- **Contexto / tarea:** Fase 5. Control de versiones y repositorio remoto.
- **Prompt utilizado:** "Verifica que los mcp, los subagentes y las skills antes de seguir con la proxima fase. No te olvides de indicarme cuando debo inicializar openspec" (verificación previa) y "Arranca con la fase 5".
- **Resumen de la respuesta:** verificación en vivo de los 3 MCP (filesystem acotado al proyecto, engram operativo, context7 resolvió Flask), 5 subagentes y 5 skills; luego `git init` + `git branch -M main`, `.gitignore` (incl. `.atl/`), 4 commits por unidad de trabajo, `gh auth login` (Franco2900), repo público `campus-virtual`, push y sincronización de `main` con `origin/main`. Se indicó que openspec se inicializa tras el OK docente y antes de CU-01.
- **Archivos modificados:** `.gitignore` (nuevo), `progreso.md`, `tiempos.md`, `prompts_log.md`, `decisiones.md` (D-008), `README.md`.
- **Resultado:** Fase 5 completada; repo `https://github.com/Franco2900/campus-virtual`.
- **Estado:** Completado.
- **Verificaciones:** `gh auth status` OK; `git status -sb` limpio y sincronizado con `origin/main`; `gh repo view` confirma `PUBLIC` y `main`.
