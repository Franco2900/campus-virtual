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
- Registrar decisiones con `decisiones.md`.

## Decision Gates

| Situación | Acción |
|-----------|--------|
| Cambia esquema de base | Delegar a subagente `database` (migración) |
| Implementación de backend | Delegar a subagente `backend` |
| Implementación de frontend | Delegar a subagente `frontend`; construir la UI sobre el design system (`src/ui/` + tokens, skill `design-system`) |
| Pruebas | Delegar a subagente `tester` |
| Captura de evidencia de UI | Playwright MCP: screenshots estandarizados `evidencias/cu-0X/NN-accion.png` en tema claro y oscuro |
| Antes de marcar Completo | Revisión con subagente `reviewer` (o skill `review-use-case` inline) y persistir `reviews/cu-0X.md` |

## Execution Steps

1. Leer el CU en `casos_de_uso.md` y el estado en `progreso.md` (solo la sección del CU activo; ver "Optimización de tokens" en AGENTS.md).
2. Diseño mínimo: modelo, flujo, endpoints afectados.
3. Implementar backend, luego frontend (sobre el design system), luego tests (delegar según tabla).
4. Verificar con `run-verification`: en iteración correr solo los tests del dominio con salida `-q`; el suite completo y el build/lint solo en el gate (ver "Optimización de tokens" en AGENTS.md).
5. Capturar evidencia: screenshots por estado clave del CU (pantalla por rol, alta/edición, error renderizado, logout) en `evidencias/cu-0X/`, en tema claro y oscuro; si el CU no es visual, evidencia = salida de smoke/tests. Gate: consola sin errores inesperados. Playwright quirúrgico: ante un paso fallido, re-capturar solo esa pantalla, no el flujo completo (ver "Optimización de tokens" en AGENTS.md).
6. Revisar con `reviewer` (o `review-use-case` inline); corregir bloqueantes y persistir `reviews/cu-0X.md` (hallazgos, severidades, veredicto, mapa de evidencia).
7. Actualizar `progreso.md`, `decisiones.md` (si hay decisión), tabla de API en `AGENTS.md`, README si corresponde. Archive del cambio openspec.
8. Si el contexto se extendió, cerrar sesión con `mem_session_summary` y retomar en una sesión nueva (ver "Fases y sesiones" en AGENTS.md).

## Output Contract

Resumen: CU, archivos modificados, verificaciones ejecutadas, evidencia y veredicto de revisión, estado final (Pendiente/En progreso/Completado/Bloqueada).