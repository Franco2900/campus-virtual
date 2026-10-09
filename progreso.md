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
| CU-01 | Registrarse | Completada | Implementado end-to-end; verificaciones y revisión pasadas; cambio `add-user-registration` archivado |
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
- **CU-01 (Registrarse) implementado end-to-end:** backend Flask (Flask 3.1.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.54, Werkzeug, pytest 9.1.1) con `POST /api/auth/register` (201/400/409, email único case-insensitive, hash de contraseña, rol Estudiante forzado) y 21 tests pasando; frontend React 19 + Vite 7 con proxy `/api` y pantalla de registro; smoke end-to-end verificado (alta 201 + duplicado 409 vía proxy). Decisión D-010.
- **CU-01 cerrado:** verificación final (pytest 21 passed, `npm run build`, smoke 201/409), revisión inline del checklist `reviewer` sin bloqueantes (el subagente `reviewer` no pudo arrancar: error de tier del proveedor, registrado en `errores.md`; el usuario aceptó la revisión inline), docs actualizadas (AGENTS, README, decisiones, progreso, prompts_log, errores, tiempos) y cambio openspec `add-user-registration` archivado como `2026-10-09-add-user-registration` (specs sincronizadas, 4 requirements; `openspec validate --specs --strict` → 1 passed). Próximo: **CU-02 (Autenticarse)** — define el mecanismo de sesión/token (diferido en CU-01).

## Próximos pasos

1. **CU-02 (Autenticarse)** orquestado por la skill `new-use-case`: define el mecanismo de sesión/token (diferido en CU-01).
2. Reintentar el subagente `reviewer` (falló por error de tier del proveedor) en próximos CU, o revisarlo en `errores.md`.

## Pendientes de definición

- Lint/formato automático.
- Organización de carpetas del frontend (parcial: definida por feature en CU-01).
- Punto de integración del chatbot.
- Convenciones de formato/indentación.
