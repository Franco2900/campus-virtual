# Registro de decisiones

Decisiones técnicas y arquitectónicas relevantes del proyecto. Evita decisiones contradictorias a futuro.

Formato:

- **ID:** identificador incremental.
- **Fecha:** `YYYY-MM-DD`.
- **Decisión:** qué se decidió.
- **Contexto / problema:** situación que la motivó.
- **Alternativas consideradas:** opciones evaluadas.
- **Criterios:** por qué se eligió.
- **Consecuencias / impacto:** efecto a corto y largo plazo.
- **Estado:** Vigente / Superada.

---

## D-001 — Stack tecnológico

- **Fecha:** 2026-10-09.
- **Decisión:** usar el stack definido en la consigna del TP: backend Python 3.14.6 + Flask, frontend React + Vite (Node v24.19.0), base SQLite con SQLAlchemy, chatbot LangChain + Ollama local.
- **Contexto / problema:** el TP define el stack; no hay libertad para reemplazarlo.
- **Alternativas consideradas:** ninguna (stack impuesto por la cátedra).
- **Criterios:** cumplimiento de la consigna.
- **Consecuencias / impacto:** las versiones exactas de librerías quedan PENDIENTE DE DEFINIR y no se cambian sin autorización.
- **Estado:** Vigente.

## D-002 — Arquitectura del backend: capas + Blueprints por dominio

- **Fecha:** 2026-10-09.
- **Decisión:** Flask con Blueprints por dominio (auth, courses, users, tasks, enrollments, grades) y separación en capas `routes → services → models`.
- **Contexto / problema:** 10 casos de uso con varios roles; se necesita una separación de responsabilidades clara para que los agentes no mezclen lógica de negocio con presentación ni con persistencia.
- **Alternativas consideradas:** (a) MVC simple de Flask (menos carpetas, se ensucia con 10 CU); (b) Clean/Hexagonal (máximo desacople, pero excesiva ceremonia para el tamaño del TP).
- **Criterios:** claridad, testeabilidad, bajo boilerplate, idoneidad para 10 CU.
- **Consecuencias / impacto:** la lógica de negocio vive en `services/`; el acceso a datos solo desde `services/` a través de los modelos; validaciones en `services/`.
- **Estado:** Vigente.

## D-003 — Servidores MCP

- **Fecha:** 2026-10-09.
- **Decisión:** usar tres servidores MCP: `engram` (memoria persistente, local), `context7` (documentación, remoto/externo) y `@modelcontextprotocol/server-filesystem` (filesystem, externo, acotado a la carpeta del proyecto). El terminal se resuelve con las herramientas nativas de opencode.
- **Contexto / problema:** el TP exige al menos 2 servidores MCP, al menos 1 externo, integrados en el flujo. Además se busca gestión de contexto de largo plazo y documentación actualizada.
- **Alternativas consideradas:** (a) solo engram + context7 (ya cumple el mínimo, menos config); (b) agregar el server-memory oficial (knowledge graph puro) además de engram; (c) agregar un MCP de terminal comunitario.
- **Criterios:** cubrir las tres categorías pedidas (memoria, filesystem/terminal, documentación), reforzar el criterio MCP del TP, evitar redundancia y riesgo.
- **Consecuencias / impacto:** opencode ya trae filesystem/terminal nativo, por lo que el MCP de filesystem es redundante en capacidades y su valor es demostrativo (sandbox con allowlist). No se usa MCP de terminal (no hay server oficial maduro). Los MCP se declaran en `opencode.json` de proyecto (Fase 2) y se documentan en el README.
- **Estado:** Vigente.

## D-004 — Medición de tiempos

- **Fecha:** 2026-10-09.
- **Decisión:** registrar los tiempos en `tiempos.md` por unidad de trabajo (wall-clock), con categorías (decisión, diseño, implementación, test, documentación, configuración, revisión) y totales acumulados.
- **Contexto / problema:** se requiere medir el tiempo total de desarrollo y desglosarlo (código, decisiones, etc.).
- **Alternativas consideradas:** (a) plugin de opencode para medir por tool-call (instrumentación automática, más precisa pero más trabajo); (b) medición manual por límites de unidad.
- **Criterios:** simplicidad, verificabilidad, disponibilidad inmediata.
- **Consecuencias / impacto:** la medición no separa con precisión "pensar" de "escribir"; queda registrado como mejora futura un plugin de instrumentación.
- **Estado:** Vigente.

## D-005 — Estrategia spec-driven y openspec

- **Fecha:** 2026-10-09.
- **Decisión:** adoptar openspec como herramienta spec-driven, a inicializar antes de comenzar la implementación de CU-01 (tras la aprobación docente de los casos de uso).
- **Contexto / problema:** se planea gestión spec-driven y hay solapamiento entre openspec y el flujo `sdd-*` disponible en el entorno.
- **Alternativas consideradas:** (a) usar el flujo `sdd-*` de gentle-ai; (b) usar openspec.
- **Criterios:** una única fuente de verdad para las specs.
- **Consecuencias / impacto:** no se corren openspec y `sdd-*` simultáneamente. `casos_de_uso.md` es la fuente de verdad actual hasta la migración.
- **Estado:** Vigente.

## D-006 — Forma del comando del MCP filesystem en Windows

- **Fecha:** 2026-10-09.
- **Decisión:** invocar el MCP `filesystem` con `["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "<ruta del proyecto>"]` y usar forward-slashes en la ruta.
- **Contexto / problema:** un spawn directo de `npx` (sin shell) falla con `ENOENT` en Windows; además, la PowerShell del sistema tiene la execution policy que bloquea `npx.ps1`/`npm.ps1`.
- **Alternativas consideradas:** (a) `["npx", "-y", ...]` (forma documentada, no resuelve en Windows sin `.cmd`); (b) ruta absoluta con backslashes (requiere escapes en JSON).
- **Criterios:** arranque garantizado en Windows, JSON limpio.
- **Consecuencias / impacto:** el comando es específico de Windows (no portable a Linux/macOS) y la ruta del proyecto es específica de esta máquina. Verificado: el server arranca y responde `Secure MCP Filesystem Server running on stdio`.
- **Estado:** Vigente.

## D-007 — Set de subagentes y skills del proyecto

- **Fecha:** 2026-10-09.
- **Decisión:** crear 5 subagentes (`backend`, `frontend`, `database`, `tester`, `reviewer` read-only) y 5 skills (`track-time`, `new-use-case`, `create-crud`, `create-migration`, `run-verification`).
- **Contexto / problema:** el TP pide roles especializados y skills reutilizables, pero advierte no crear por cumplir una lista.
- **Alternativas consideradas:** (a) los 6 subagentes de la plantilla (incluye `architect`); (b) crear skills por cada patrón visible (se descartaron `create-react-page`, `log-decision` y `generate-docs` por estar absorbidos por `create-crud`/`new-use-case`/las subagentes); (c) este set mínimo.
- **Criterios:** que cada skill resuelva una tarea concreta y repetitiva sin duplicarse; que cada subagente tenga una responsabilidad no solapada; el `architect` se omite porque el diseño de contrato ya está en `casos_de_uso.md` + `AGENTS.md`.
- **Consecuencias / impacto:** el flujo por CU queda orquestado por `new-use-case`, que delega al resto; `reviewer` es obligatorio antes de marcar un CU como Completo. Si un patrón se repite, se recomienda una skill nueva.
- **Estado:** Vigente.
