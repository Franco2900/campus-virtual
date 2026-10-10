# Control de progreso

Estados permitidos: **Pendiente** | **En progreso** | **Completada** | **Bloqueada**.

Última actualización: 2026-10-10.

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
| CU-02 | Autenticarse | Completada | Implementado end-to-end; smoke HTTP 10/10 + UI Playwright; revisión APROBADA; cambio `2026-10-10-add-user-auth` archivado |
| CU-03 | Gestionar cursos | Completada | Implementado end-to-end; smoke 13/13 + UI Playwright; revisión APROBADA; cambio `2026-10-10-add-course-management` archivado |
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
- **CU-02 (Autenticarse) implementado y verificado:** API `POST /api/auth/login` (cookie de sesión firmada de Flask, D-011), `GET /api/auth/me` (protegido por `@login_required`) y `POST /api/auth/logout` (idempotente). Backend con 32 tests en `backend/tests/test_auth.py`; frontend con pantalla de login con toggle a registro y barra de sesión (nombre + rol + "Cerrar sesión"); smoke end-to-end **10/10 PASS** vía `scripts/verify.py` (readiness + proxy + cleanup garantizado) y smoke de UI con Playwright (registro → login → header con rol Estudiante → logout → error renderizado del backend) con screenshots en `evidencias/cu-02/`. Cierre: revisión APROBADA, cambio `add-user-auth` archivado y commits finales.
- **Gotcha de tooling resuelto:** en Windows, terminar `npm.cmd` dejaba el `node vite` hijo huérfano escuchando en `:5173`; los servicios lanzados no sobreviven a un reinicio de opencode ni a un tool call abortado. Solución: `scripts/verify.py` (**generalizado**, `--cu` y `--diagnose` para diagnóstico read-only) con pre-condición de puertos libres y cleanup del árbol de procesos (ver `errores.md`).
- **CU-02 cerrado:** backtrack 6.1 y 6.2 `[x]`, smoke HTTP 10/10 PASS y smoke de UI con Playwright (4 screenshots en `evidencias/cu-02/`), revisión del checklist `reviewer` sin bloqueantes (el subagente `reviewer` volvió a fallar por tier del proveedor; revisión inline aceptada), cambio `add-user-auth` archivado como `2026-10-10-add-user-auth` (`openspec validate --specs --strict` → 1 passed) y 6 commits por unidad de trabajo. Próximo: **CU-03 (Gestionar cursos)**.
- **CU-03 (Gestionar cursos) implementado y verificado (cierre en curso):** ciclo spec-driven `add-course-management` (proposal/specs/design/tasks). Backend: modelo `Course` (`code` único case-insensitive, `active` con baja lógica), `course_service` con validaciones en `services/` (400/403/404/409) y blueprint `courses` (`GET/POST /api/courses`, `GET/PUT/PATCH /api/courses/<id>`) protegido por `@login_required` + `@require_roles(UserRole.ADMIN)`. Bootstrap del Administrador con `scripts/seed_admin.py` (env obligatorio, idempotente, 4 cursos demo) — D-017. Frontend: ruteo con `react-router-dom` y pantalla de cursos (listado con estado, alta, edición, activar/desactivar) — D-018. Verificación: **55 tests** backend, `npm run build` + Prettier OK, smoke end-to-end **13/13 PASS** y evidencia UI Playwright (7 screenshots en `evidencias/cu-03/`). `scripts/verify.py` ahora corre contra una **base temporal aislada** con seed del admin.
- **Bug detectado y corregido vía evidencia UI:** el registro no emite cookie de sesión, pero el frontend asumía sesión al registrar; se corrigió para navegar a `/login` tras el registro (ver D-018).
- **CU-03 cerrado:** revisión APROBADA (skill `review-use-case` inline, sin bloqueantes; `reviews/cu-03.md`), cambio archivado como `2026-10-10-add-course-management` (`openspec validate --specs --strict` → 2 passed), y commits por unidad de trabajo. Próximo: **CU-04 (Gestionar usuarios)**.

## Próximos pasos

1. **CU-04 (Gestionar usuarios)** orquestado por la skill `new-use-case`.
2. Resolver el tier del proveedor para el subagente `reviewer` (falló en CU-01, CU-02 y CU-03; se cerró con revisión inline) y reintentarlo en el próximo CU.

## Pendientes de definición

- Lint/formato automático.
- Organización de carpetas del frontend (parcial: definida por feature en CU-01).
- Punto de integración del chatbot.
- Convenciones de formato/indentación.
