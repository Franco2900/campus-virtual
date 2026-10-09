---
name: track-time
description: "Trigger: medir tiempo, registrar tiempo, iniciar/terminar tarea, actualizar tiempos.md. Registra intervalos de trabajo en tiempos.md con categoría, duración y totales."
license: MIT
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar cuando se inicia o finaliza una unidad de trabajo (tarea, caso de uso, decisión, verificación) o cuando se pide actualizar `tiempos.md`.

## Hard Rules

- Usar formato ISO 8601 local: `YYYY-MM-DDTHH:MM:SS`.
- Duración = Fin - Inicio, formato `HH:MM:SS`.
- Cada fila lleva categoría del listado (DEC/DIS/IMP/TST/DOC/CFG/REV) y Actor (Humano/Agente/Humano+Agente).
- Actualizar SIEMPRE la sección de Totales al agregar una fila.
- No inventar marcas: si falta inicio o fin, registrarlo como pendiente.

## Execution Steps

1. Capturar la marca de inicio (`Get-Date -Format "yyyy-MM-ddTHH:mm:ss"` en Windows PowerShell; `date +"%Y-%m-%dT%H:%M:%S"` en Linux/macOS).
2. Al terminar, capturar la de fin y restar para la duración.
3. Agregar la fila a la tabla Registro.
4. Actualizar Totales por categoría y el total general.
5. Reportar la duración en el resumen.

## Output Contract

Folder `tiempos.md` actualizado + duración del intervalo reportada en la respuesta.