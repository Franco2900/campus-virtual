# Control de progreso

Estados permitidos: **Pendiente** | **En progreso** | **Completada** | **Bloqueada**.

Última actualización: 2026-10-09.

## Fases de configuración del entorno

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 1 | Documentación base (`AGENTS.md`, `README.md`, `casos_de_uso.md`, registros) | Completada |
| Fase 2 | `opencode.json` de proyecto (MCP filesystem, permisos) | Completada |
| Fase 3 | Subagentes especializados en `.opencode/agents/` | Completada |
| Fase 4 | Skills reutilizables en `.opencode/skills/` | Completada |
| Fase 5 | Git + repositorio en GitHub | Completada |
| Fase 6 | Implementación de casos de uso (requiere OK docente y openspec inicializado) | Bloqueada |

## Casos de uso

| ID | Nombre | Estado | Notas |
|----|--------|--------|-------|
| CU-01 | Registrarse | Pendiente | Bloqueado hasta OK docente |
| CU-02 | Autenticarse | Pendiente | Bloqueado hasta OK docente |
| CU-03 | Gestionar cursos | Pendiente | Bloqueado hasta OK docente |
| CU-04 | Gestionar usuarios | Pendiente | Bloqueado hasta OK docente |
| CU-05 | Gestionar inscripciones | Pendiente | Bloqueado hasta OK docente |
| CU-06 | Gestionar tareas | Pendiente | Bloqueado hasta OK docente |
| CU-07 | Entregar tarea | Pendiente | Bloqueado hasta OK docente |
| CU-08 | Corregir tarea | Pendiente | Bloqueado hasta OK docente |
| CU-09 | Consultar calificaciones | Pendiente | Bloqueado hasta OK docente |
| CU-10 | Filtrar usuarios | Pendiente | Bloqueado hasta OK docente |

## Resumen del agente (último)

- Fase 1 completada: documentación base del proyecto creada.
- Fase 2 completada: `opencode.json` de proyecto con el MCP `filesystem` (comando `cmd /c npx -y @modelcontextprotocol/server-filesystem`) y bloque de permisos. MCPs documentados en el README.
- Fase 3 completada: subagentes `backend`, `frontend`, `database`, `tester`, `reviewer` (read-only) en `.opencode/agents/`.
- Fase 4 completada: skills `track-time`, `new-use-case`, `create-crud`, `create-migration`, `run-verification` en `.opencode/skills/`. Registro actualizado en `.atl/skill-registry.md`.
- Fase 5 completada: repo `main` en GitHub **público** `https://github.com/Franco2900/campus-virtual` con 4 commits por unidad de trabajo (`chore`, `docs` x2, `feat`). Verificación previa OK: MCP `filesystem` conectado y acotado al proyecto, `context7` respondiendo, 5 subagentes y 5 skills registrados.
- Decisiones registradas en `decisiones.md` (stack, arquitectura, MCPs, tiempos, openspec, comando MCP, set de skills/agentes, repo).
- Los casos de uso quedaron especificados en `casos_de_uso.md`.

## Próximos pasos

1. **Obtener el OK docente sobre los 10 casos de uso** (condición habilitante; sin esto no se codea).
2. **Inicializar openspec** — paso cero de la Fase 6, antes de implementar CU-01 (ver D-005).
3. Implementar los casos de uso orquestados por `new-use-case` (Fase 6).

## Pendientes de definición

- Versiones exactas de librerías (Flask, SQLAlchemy, React, Vite, LangChain).
- Organización de carpetas del frontend.
- Punto de integración del chatbot.
- Comandos reales de ejecución, test y lint.
- Convenciones de formato/indentación.
