---
name: run-verification
description: "Trigger: verificar, correr tests, ejecutar pytest, npm run build/build, smoke test, comprobar que funcione. Ejecuta la verificación mínima y reproducible de un cambio."
license: MIT
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar ante cualquier "¿funciona?", "verificá", "corré los tests" o antes de declarar un cambio como terminado.

## Hard Rules

- NO inventar comandos: leer la sección "Cómo ejecutar" de `AGENTS.md` (los comandos reales se definen en Fase 6).
- Ejecutar primero la verificación más pequeña y relevante; luego las generales.
- No afirmar que un test pasa o un build funciona sin haberlo ejecutado.
- Conservar los mensajes de error completos y registrar en `errores.md` los fallos relevantes.

## Execution Steps

1. Leer comandos reales de backend/frontend/tests en `AGENTS.md`.
2. Correr la verificación más acotada al cambio.
3. Correr la suite general (si existe) y el build.
4. Reportar: comandos ejecutados, resultados, y en caso de falla, el error exacto.

## Output Contract

Lista de comandos ejecutados con su resultado (OK/FAIL) y, si falló, el mensaje de error completo y el estado (Resuelto/Pendiente).