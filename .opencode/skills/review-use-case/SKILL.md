---
name: review-use-case
description: "Trigger: revisar el caso de uso, checklist del revisor, verificar que el CU esté completo, ¿está listo para marcar Completo?. Ejecuta el checklist de revisión de un CU del Campus Virtual con gate de evidencia."
license: Apache-2.0
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar antes de marcar un CU como Completo, ante "revisar", "checklist del revisor", "verificar el CU" o cuando el subagente `reviewer` no esté disponible (falla de tier del proveedor).

## Hard Rules

- Revisión de solo lectura: nunca editar código ni documentación.
- Cada hallazgo verificable con `archivo:línea`, severidad (Bloqueante/Alta/Media/Baja) y evidencia concreta.
- APROBADO solo si no hay bloqueantes y el CU cumple `casos_de_uso.md` (flujo principal + alternativos + errores) y las reglas de negocio de `AGENTS.md`.
- No afirmar PASS sin evidencia: salida real de comandos o screenshots.

## Execution Steps

1. Leer el CU en `casos_de_uso.md`, las "Reglas de negocio clave" de `AGENTS.md` y el estado en `progreso.md`.
2. Verificar arquitectura: `routes → services → models`; sin lógica de negocio ni SQL crudo en `routes/`.
3. Verificar autorización por rol en cada endpoint nuevo y ausencia de secretos en el código.
4. Gate de evidencia: confirmar screenshots estandarizados en `evidencias/cu-0X/` (`NN-accion.png`, full-page cuando aporte) que muestren el estado esperado, o salida de smoke/tests si el CU no es visual; consola sin errores inesperados.
5. Comparar documentación: tabla de API en `docs/api.md`, `progreso.md`, README y specs openspec.
6. Emitir APROBADO/RECHAZADO y pedir al orquestador que persista `reviews/cu-0X.md` (hallazgos, severidades, veredicto, mapa de evidencia).

## Output Contract

Hallazgos `archivo:línea` + severidad + evidencia; veredicto APROBADO/RECHAZADO; lista de evidencias verificadas (existen y muestran el estado esperado).

## References

- `.opencode/agents/reviewer.md` — checklist equivalente en el subagente read-only.