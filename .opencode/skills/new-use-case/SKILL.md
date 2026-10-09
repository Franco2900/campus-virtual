---
name: new-use-case
description: "Trigger: implementar CU, arrancar el caso de uso, desarrollar XX-0X, completar un caso de uso. Orquesta el ciclo completo de un caso de uso del Campus Virtual."
license: MIT
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar cuando se trabaja sobre un caso de uso específico del proyecto (CU-01..CU-10), tanto para planificar como para implementar.

## Hard Rules

- Trabajar UN caso de uso a la vez.
- No marcar un CU como Completado sin: funcionalidad implementada, código ejecutándose, tests ejecutados, documentación y progreso actualizados.
- Respetar reglas de negocio de `casos_de_uso.md` y la arquitectura de `AGENTS.md` (routes → services → models).
- Registrar tiempos con la skill `track-time` y decisiones con `decisiones.md`.

## Decision Gates

| Situación | Acción |
|-----------|--------|
| Cambia esquema de base | Delegar a subagente `database` (migración) |
| Implementación de backend | Delegar a subagente `backend` |
| Implementación de frontend | Delegar a subagente `frontend` |
| Pruebas | Delegar a subagente `tester` |
| Antes de marcar Completo | Delegar revisión al subagente `reviewer` |

## Execution Steps

1. Leer el CU en `casos_de_uso.md` y el estado en `progreso.md`.
2. Arrancar `track-time`.
3. Diseño mínimo: modelo, flujo, endpoints afectados.
4. Implementar backend, luego frontend, luego tests (delegar según tabla).
5. Verificar con `run-verification`.
6. Revisar con `reviewer`; corregir lo bloqueante.
7. Actualizar `progreso.md`, `decisiones.md` (si hay decisión), tabla de API en `AGENTS.md`, README si corresponde, `prompts_log.md`.
8. Cerrar `track-time`.

## Output Contract

Resumen: CU, archivos modificados, verificaciones ejecutadas, estado final (Pendiente/En progreso/Completado/Bloqueada).