# Registro de decisiones

Decisiones técnicas y arquitectónicas del proyecto, partidas por caso de uso para mantener cada archivo chico y cargar solo lo relevante. Evita decisiones contradictorias a futuro.

## Formato

- **ID:** identificador incremental (el número es global y no se reutiliza).
- **Fecha:** `YYYY-MM-DD`.
- **Decisión:** qué se decidió.
- **Contexto / problema:** situación que la motivó.
- **Alternativas consideradas:** opciones evaluadas.
- **Criterios:** por qué se eligió.
- **Consecuencias / impacto:** efecto a corto y largo plazo.
- **Estado:** Vigente / Superada / Acordada / Abierto.

## Índice

| Archivo | Alcance | IDs |
|---------|---------|-----|
| [`00-general.md`](./00-general.md) | Decisiones transversales de proyecto y tooling (no atadas a un CU) | D-001–D-009, D-012–D-017, D-019, D-020, D-023, D-028, D-029, D-036, D-042 |
| [`cu-01.md`](./cu-01.md) | Registrarse | D-010 |
| [`cu-02.md`](./cu-02.md) | Autenticarse | D-011, D-018 |
| [`cu-04.md`](./cu-04.md) | Gestionar usuarios (incluye relación Profesor↔curso) | D-021, D-022 |
| [`cu-05.md`](./cu-05.md) | Gestionar inscripciones | D-024, D-025 |
| [`cu-06.md`](./cu-06.md) | Gestionar tareas | D-026, D-027 |
| [`cu-07.md`](./cu-07.md) | Entregar tarea | D-030, D-031 |
| [`cu-08.md`](./cu-08.md) | Corregir tarea | D-032, D-033 |
| [`cu-09.md`](./cu-09.md) | Consultar calificaciones | D-034, D-035, D-041 |
| [`cu-10.md`](./cu-10.md) | Filtrar usuarios | D-037, D-038 |
| [`cu-11.md`](./cu-11.md) | Utilizar chatbot de asistencia | D-039, D-040, D-043 |
| [`cu-12.md`](./cu-12.md) | Gestionar fuentes de conocimiento del chatbot | D-044–D-048 |

> No hay archivo `cu-03.md`: las decisiones de CU-03 (gestión de cursos) quedaron como transversales de arquitectura en `00-general.md` (la especificación de curso y su gestión se fijaron junto al scaffolding). Si CU-03 recibe decisiones propias nuevas, se crea su archivo y se agrega la fila.

## Criterios de reparto

- **`00-general.md`:** decisiones que no pertenecen a un CU puntual — stack, arquitectura, MCP, CI, tooling, proceso y eliminaciones de infraestructura.
- **Por CU:** decisiones de alcance, modelo, endpoints y UI de ese caso de uso.
- Al agregar una decisión nueva, va al archivo del CU correspondiente (o a `00-general.md` si es transversal) y se actualiza la fila del índice.
