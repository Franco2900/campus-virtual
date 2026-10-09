# AGENTS.md

Instrucciones persistentes para agentes de IA (opencode) que trabajan en este proyecto.
Este archivo es la fuente de verdad operativa. El README es para humanos.

## Proyecto

- **Nombre:** Campus Virtual.
- **Propósito:** sistema web completo (backend + frontend) que gestiona cursos, usuarios, inscripciones, tareas y calificaciones con tres roles (Estudiante, Profesor, Administrador) y un chatbot integrado.
- **Contexto:** Trabajo Práctico Integrador (UNLa), Grupo 12. El foco de evaluación es la orquestación de AI Engineering y la funcionalidad, no la estética.
- **Componentes:** backend Flask (API REST), frontend React + Vite, base SQLite vía SQLAlchemy, chatbot LangChain + Ollama local.

## Cómo ejecutar

> PENDIENTE DE DEFINIR: los comandos reales se completan cuando exista el código (Fase 6). No ejecutar comandos inventados.

- **Backend (dev):** PENDIENTE DE DEFINIR (esperado: entorno virtual + `pip install -r requirements.txt` + `python app.py`).
- **Frontend (dev):** PENDIENTE DE DEFINIR (esperado: `npm install` + `npm run dev`).
- **Tests:** PENDIENTE DE DEFINIR (esperado: `pytest` en backend).
- **Lint / formato:** PENDIENTE DE DEFINIR.
- Se actualiza esta sección en cuanto los comandos existan y sean verificables.

## Arquitectura

- **Patrón:** capas + Blueprints por dominio (Flask).
- **Regla de dependencias:** `routes → services → models`. La lógica de negocio vive en `services/`, nunca en `routes/` ni en los modelos.
- **Estructura backend:**

```
backend/
├── app.py            # factory: crea la app, registra blueprints, inicializa DB
├── blueprints/       # una por dominio: auth, courses, users, tasks, enrollments, grades
├── services/         # lógica de negocio y validaciones
├── models/           # entidades SQLAlchemy
└── config/           # configuración (DB path, secretos por env)
```

- **Persistencia:** toda consulta a la base se hace desde `services/` a través de los modelos SQLAlchemy. No hay SQL crudo en `routes/`.
- **Validaciones:** en la capa `services/`.
- **Frontend:** PENDIENTE DE DEFINIR la organización de carpetas (esperado: por feature o por tipo, a definir antes de CU-01).
- **Chatbot:** PENDIENTE DE DEFINIR el punto de integración con LangChain + Ollama.

## Casos de uso

Resumen (detalle completo en `casos_de_uso.md`):

| ID | Nombre | Actor |
|----|--------|-------|
| CU-01 | Registrarse | Usuario no registrado |
| CU-02 | Autenticarse | Usuario |
| CU-03 | Gestionar cursos | Administrador |
| CU-04 | Gestionar usuarios | Administrador |
| CU-05 | Gestionar inscripciones | Administrador / Profesor |
| CU-06 | Gestionar tareas | Profesor |
| CU-07 | Entregar tarea | Estudiante |
| CU-08 | Corregir tarea | Profesor |
| CU-09 | Consultar calificaciones | Profesor / Estudiante |
| CU-10 | Filtrar usuarios | Administrador |

### Reglas de negocio clave

- Cada usuario tiene **exactamente un rol** (mutuamente excluyentes). Los nuevos son Estudiante; Profesor lo asigna un Administrador.
- El correo electrónico es identificador único de la cuenta.
- Cursos y tareas pueden estar activos o inactivos; los inactivos no se tratan como activos.
- Calificaciones entre 1 y 10. Promedio simple. Tareas no corregidas no entran al promedio; tareas no entregadas fuera de plazo cuentan como 1.
- Un Profesor solo opera sobre los cursos en los que trabaja.
- Inscripciones, modificaciones de tareas y correcciones **no** generan notificaciones por correo.

## Mapa de archivos

```
/
├── AGENTS.md            # este archivo (instrucciones para agentes)
├── README.md            # documentación para humanos
├── opencode.json        # configuración de proyecto (MCP, permisos)
├── casos_de_uso.md      # especificación de los 10 CU
├── decisiones.md        # registro de decisiones técnicas/arquitectónicas
├── errores.md           # bitácora de errores
├── progreso.md          # control de progreso
├── prompts_log.md       # auditoría de prompts
├── tiempos.md           # medición de tiempos de desarrollo
├── backend/             # PENDIENTE DE DEFINIR (Fase 6)
├── frontend/            # PENDIENTE DE DEFINIR (Fase 6)
├── openspec/            # specs spec-driven (openspec): fuente de verdad de specs
├── .atl/
│   └── skill-registry.md  # índice de skills (generado)
└── .opencode/
    ├── agents/          # subagentes: backend, frontend, database, tester, reviewer
    ├── commands/        # comandos /opsx-* del CLI openspec (generados)
    └── skills/          # skills: track-time, new-use-case, create-crud, create-migration, run-verification, openspec-*
```

> No documentar ni referenciar archivos que no existan todavía.

## API

> PENDIENTE DE DEFINIR. No inventar endpoints. La tabla se completa a medida que se implementan.

| Método | Ruta | CU | Propósito | Auth |
|--------|------|----|-----------|------|
| - | - | - | (vacío hasta Fase 6) | - |

## Convenciones

> PENDIENTE DE DEFINIR los detalles. Reglas mínimas ya fijadas:

- **Idioma del código e identificadores:** inglés.
- **Idioma de la documentación (README, AGENTS, docs):** español (neutral).
- **Backend:** `snake_case` para variables y funciones, `PascalCase` para clases, archivos en `snake_case`.
- **Frontend:** PENDIENTE DE DEFINIR (esperado: `camelCase`/`PascalCase`, componentes `PascalCase`).
- **Comentarios:** ninguno por defecto. Solo cuando expliquen una decisión, restricción o comportamiento no evidente.
- **Indentación / formato:** PENDIENTE DE DEFINIR (esperado: formateador automático).

## Verificación

> PENDIENTE DE DEFINIR: se completa con comandos reales en Fase 6.

- No declarar una tarea completada sin haber ejecutado su verificación.
- Conservar mensajes de error completos.
- Un CU se considera Completo solo cuando: funcionalidad implementada, código ejecutando, tests ejecutados, documentación y `progreso.md` actualizados (ver criterios en la plantilla).

## Portabilidad

- **Objetivo:** el sistema (backend + frontend) debe correr en **Windows, Linux y macOS** con los pasos de "Cómo ejecutar".
- Rutas relativas al proyecto; sin rutas absolutas en el código de la app.
- Sin comandos, separadores ni rutas exclusivos de una plataforma en el código y scripts de la app.
- Documentar los requisitos específicos por SO cuando existan.
- La configuración local de herramientas (p. ej. `opencode.json`: ruta del MCP filesystem y forma del comando) es **tooling específico de la máquina**, no forma parte del sistema portable. No replicar patrones de esa config en el código de la app.

## Roadmap

- **Ahora:** Fase 6 en marcha — openspec inicializado (`openspec/` + `config.yaml`), OK docente obtenido. Próximo: CU-01 orquestado por `new-use-case`.
- **Activo:** pipeline spec-driven por CU vía `new-use-case` (propose → specs → design → tasks → apply → verify → archive) con `reviewer` antes de marcar Completo.
- **Futuro:** plugin de opencode para medir tiempos por tool-call de forma automática.
- **Futuro:** chatbot LangChain + Ollama integrado en la app.
- **Pendiente:** definir versiones exactas de librerías y comandos reales de ejecución/test al arrancar CU-01.

## Límites

- No reemplazar tecnologías ni versiones del stack sin autorización.
- No introducir dependencias nuevas si ya existe una adecuada.
- No rediseñar la arquitectura existente por preferencia personal.
- No implementar funcionalidad fuera del alcance de los 10 CU.
- No tocar archivos marcados como generados (cuando existan).

## MCP y herramientas

- **engram** (memoria, local, config global): memoria persistente del proyecto. Usar para recordar decisiones y gotchas; no reemplaza a `decisiones.md`/`progreso.md`.
- **context7** (documentación, remoto/externo, config global): consultar docs actualizadas antes de escribir código de librerías (Flask, SQLAlchemy, React, Vite, LangChain). Evita APIs inventadas.
- **filesystem** (local, `opencode.json`): acceso a archivos acotado a la carpeta del proyecto.
- **Terminal:** herramienta nativa de opencode.
- **openspec CLI** (spec-driven): herramienta nativa del CLI; en Windows invocar siempre `cmd /c openspec ...` (mismo bloqueo de execution policy que `npx`, ver D-006). Los comandos `/opsx-*` omiten esa complejidad.
- Requisito de la consigna: mínimo 2 servidores MCP, al menos 1 externo (se cumple con engram + context7 + filesystem).

## Skills y subagentes

Skills del proyecto (`.opencode/skills/`, registradas en `.atl/skill-registry.md`):

| Skill | Cuándo |
|-------|--------|
| `track-time` | Iniciar/cerrar unidades de trabajo y actualizar `tiempos.md` |
| `new-use-case` | Ciclo completo de un CU (planificar e implementar) |
| `create-crud` | Abm/CRUD de una entidad (modelo + servicio + rutas + React) |
| `create-migration` | Cambios de esquema con migraciones |
| `run-verification` | Verificar tests/build antes de declarar algo terminado |
| `openspec-*` (6) | Vía nativa del CLI openspec: propose, explore, update-change, apply-change, sync-specs, archive-change (comandos `/opsx-*`) |

Subagentes (`.opencode/agents/`): `backend`, `frontend`, `database`, `tester`, `reviewer` (read-only). Usarlos delegando trabajo específico; el `reviewer` es obligatorio antes de marcar un CU como Completo.

Recomendar skills y subagentes nuevos cuando un patrón se repita o una tarea sea recurrente; no crear por cumplir inventario.

## Seguridad y gotchas

- **Nunca** escribir secretos, tokens ni credenciales en el código; usar variables de entorno.
- **Nunca** almacenar credenciales en archivos del proyecto.
- No ejecutar operaciones destructivas sobre datos sin autorización explícita.
- No desactivar autenticación/autorización para "probar".
- No exponer datos sensibles en logs.
- Gotcha de negocio: respetar estrictamente la exclusividad de roles y el identificador único de email.
- Gotcha de plazo: las entregas/modificaciones de CU-07 y CU-08 dependen de fecha límite y estado de corrección; validarlo en `services/`, no en el cliente.
