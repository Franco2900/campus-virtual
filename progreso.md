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
| Fase 6 | Implementación de casos de uso (requiere OK docente y openspec inicializado) | En progreso |

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
- **OK docente obtenido** para los 10 casos de uso (condición habilitante).
- Paso cero de la Fase 6: **openspec inicializado** (`openspec init` v1.13.2 con `--tools opencode --language es`): `openspec/config.yaml` (context, `strict_tdd: false` hasta que exista runner de tests, reglas por fase) + integración nativa para opencode (6 skills `openspec-*` y 6 comandos `/opsx-*`). Verificado: `openspec list` resuelve el root del proyecto, sin cambios activos.
- Decisiones registradas en `decisiones.md` (stack, arquitectura, MCPs, tiempos, openspec, comando MCP, set de skills/agentes, repo, operación de openspec).
- Los casos de uso quedaron especificados en `casos_de_uso.md`.

## Próximos pasos

1. **CU-01 (Registrarse)** orquestado por la skill `new-use-case`: propose → specs → design → tasks → apply → verify → archive, delegando en los subagentes (`reviewer` obligatorio antes de marcar Completo). `track-time` en cada unidad; definir versiones de librerías y comandos de ejecución/test al arrancar.
2. Definir el stack Python (venv + `requirements.txt`) y el scaffolding del backend al implementar CU-01.

## Pendientes de definición

- Versiones exactas de librerías (Flask, SQLAlchemy, React, Vite, LangChain).
- Organización de carpetas del frontend.
- Punto de integración del chatbot.
- Comandos reales de ejecución, test y lint.
- Convenciones de formato/indentación.
