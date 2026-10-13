# Spec Delta

## MODIFIED Requirements

### Requirement: Cursos disponibles para gestionar inscripciones

El sistema SHALL permitir consultar, mediante `GET /api/courses/mine`, los cursos sobre los que el usuario autenticado puede operar según su rol: para un Profesor, únicamente aquellos en los que está asignado; para un Administrador, todos los cursos del sistema; para un Estudiante, aquellos en los que tiene una inscripción activa. La respuesta MUST incluir los cursos junto con su estado activo/inactivo. Un request sin sesión MUST responder HTTP 401.

#### Scenario: Cursos de un Profesor
- **GIVEN** que un Profesor tiene sesión activa y está asignado a uno o más cursos
- **WHEN** el Profesor envía `GET /api/courses/mine`
- **THEN** el sistema responde HTTP 200 con únicamente los cursos en los que está asignado

#### Scenario: Profesor sin cursos asignados
- **GIVEN** que un Profesor tiene sesión activa y no está asignado a ningún curso
- **WHEN** el Profesor envía `GET /api/courses/mine`
- **THEN** el sistema responde HTTP 200 con una lista vacía

#### Scenario: Cursos de un Administrador
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** envía `GET /api/courses/mine`
- **THEN** el sistema responde HTTP 200 con todos los cursos del sistema

#### Scenario: Cursos de un Estudiante
- **GIVEN** que un Estudiante tiene sesión activa y tiene inscripciones activas e inactivas en distintos cursos
- **WHEN** el Estudiante envía `GET /api/courses/mine`
- **THEN** el sistema responde HTTP 200 con únicamente los cursos en los que su inscripción está activa

#### Scenario: Estudiante sin inscripciones activas
- **GIVEN** que un Estudiante tiene sesión activa pero ninguna inscripción activa
- **WHEN** el Estudiante envía `GET /api/courses/mine`
- **THEN** el sistema responde HTTP 200 con una lista vacía
