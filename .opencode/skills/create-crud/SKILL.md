---
name: create-crud
description: "Trigger: crear CRUD, crear endpoints para, modelo + rutas, ABM de. Genera un CRUD completo (modelo, servicio, blueprint, pantalla React y cliente de API) siguiendo los patrones existentes."
license: MIT
metadata:
  author: "Franco2900"
  version: "1.0"
---

## Activation Contract

Cargar cuando se pide un ABM/CRUD de una entidad (curso, usuario, tarea, inscripción, etc.) en el Campus Virtual.

## Hard Rules

- Inspeccionar primero los CRUD existentes y replicar sus patrones (no inventar estructura).
- No inventar tablas, columnas ni endpoints: el contrato surge del CU y del esquema real.
- Orden: modelo → servicio (validaciones) → blueprint (rutas) → pantalla React → cliente de API.
- Reglas de negocio en `services/`, nunca en rutas ni en el cliente.

## Decision Gates

| Entidad | Aplicar |
|---------|---------|
| Existe el modelo | Crear solo servicio + rutas + UI |
| No existe el modelo | Crear modelo (o migración) + resto |
| Solo backend | Omitir pantalla y cliente React |

## Execution Steps

1. Leer el CU y el esquema/modelos reales.
2. Crear/ajustar modelo y validaciones en el servicio.
3. Crear rutas del blueprint correspondiente y registrar la API (tabla de `AGENTS.md`).
4. Crear pantalla React + consumo del cliente de API.
5. Verificar con `run-verification`.

## Output Contract

Lista de archivos creados/modificados + tabla de rutas nuevas (método, path, CU, auth).