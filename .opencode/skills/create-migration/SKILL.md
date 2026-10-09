---
name: create-migration
description: "Trigger: migración, cambiar esquema, agregar columna, modificar tabla. Crea una migración de esquema consistente con el modelo SQLAlchemy."
license: MIT
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar cuando un cambio requiere modificar tablas y el proyecto usa migraciones (verificar en `AGENTS.md`/setup antes de asumir).

## Hard Rules

- Verificar primero si el proyecto tiene migraciones configuradas; si no, informarlo y no inventar la herramienta.
- No ejecutar operaciones destructivas (drop table/column, delete masivo) sin autorización explícita.
- La migración debe reflejar exactamente el modelo; modelo y esquema no pueden divergir.
- Conservar mensajes de error completos ante fallas.

## Execution Steps

1. Leer el cambio de modelo y el esquema actual real.
2. Generar la migración con la herramienta del proyecto (p. ej., Alembic: `alembic revision --autogenerate -m "<desc>"`).
3. Revisar la migración generada antes de aplicarla (autogenerate puede traer ruido).
4. Aplicarla (`alembic upgrade head`) y verificar el esquema resultante.
5. Documentar el cambio en `decisiones.md`/`progreso.md` cuando corresponda.

## Output Contract

Archivo de migración + resumen del cambio de esquema + comando ejecutado y su resultado.