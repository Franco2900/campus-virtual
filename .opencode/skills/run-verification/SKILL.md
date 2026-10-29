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

- NO inventar comandos: leer los `AGENTS.md` (el compartido en la raíz y el de la capa que toques: `backend/AGENTS.md` / `frontend/AGENTS.md`) para los comandos reales y verificados del proyecto.
- Frontend: `npm run build` + `npm run lint:format` (Windows con prefijo `cmd /c`).
- Ejecutar primero la verificación más pequeña y relevante; luego las generales.
- No afirmar que un test pasa o un build funciona sin haberlo ejecutado.
- Conservar los mensajes de error completos y registrar en `errores/` los fallos relevantes.

## Execution Steps

1. Leer los comandos reales: los compartidos en `AGENTS.md`, los de backend en `backend/AGENTS.md` y los de frontend en `frontend/AGENTS.md`.
2. Correr la verificación más acotada al cambio (web: `npm run build` y `npm run lint:format`; backend: el subconjunto de tests relevante).
3. Correr la suite general (smoke con `scripts/verify.py --cu CU-0X` cuando aplique y el build del frontend).
4. Reportar: comandos ejecutados, resultados, y en caso de falla, el error exacto.

## Output Contract

Lista de comandos ejecutados con su resultado (OK/FAIL) y, si falló, el mensaje de error completo y el estado (Resuelto/Pendiente).