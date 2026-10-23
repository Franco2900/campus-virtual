# Bitácora de errores

Registro de errores relevantes del proyecto, partidos por caso de uso para mantener cada archivo chico y cargar solo lo relevante. Evita repetir diagnósticos.

## Formato de cada entrada

- **Fecha:** `YYYY-MM-DD`.
- **Error exacto:** mensaje completo (sin recortar).
- **Contexto:** qué se estaba haciendo y con qué herramienta/versión.
- **Causa probable:** hipótesis (diferenciar confirmada vs. probable).
- **Archivos involucrados:** rutas.
- **Diagnóstico:** pasos realizados (reproducibles).
- **Solución aplicada:** cambio mínimo.
- **Verificación posterior:** cómo se confirmó la corrección.
- **Estado final:** Resuelto / Pendiente / Abierto.

## Índice

| Archivo | Alcance | Entradas |
|---------|---------|----------|
| [`00-general.md`](./00-general.md) | Errores transversales: harness de smoke/dev, tooling de revisión, evidencia y entorno (no atados a un CU) | `reviewer` por tier (×3), percepción de congelamiento, Vite huérfano, tool call en primer plano, gaps de Playwright con el tema, Prettier y CRLF |
| [`cu-01.md`](./cu-01.md) | Registrarse | Conexión cerrada en el primer request proxeado por Vite (race de arranque del smoke) |
| [`cu-04.md`](./cu-04.md) | Gestionar usuarios | Error de consola al anidar dos `Modal` de Bootstrap |

> Sin archivo por CU para el resto: los casos de uso posteriores no registraron errores propios (los problemas fueron de harness/tooling y quedaron en `00-general.md`). Al registrar un error nuevo, va al archivo del CU correspondiente (o a `00-general.md` si es transversal) y se actualiza la fila del índice.
