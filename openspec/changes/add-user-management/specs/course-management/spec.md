# Spec Delta

## Purpose

Extender la gestión de cursos con la asignación y remoción de profesores por curso (relación profesor↔curso), operación exclusiva del Administrador, para que el sistema conozca qué profesores trabajan en cada curso.

## ADDED Requirements

### Requirement: Asignación de profesores a un curso

El sistema SHALL permitir al Administrador asignar una cuenta con rol Profesor a un curso existente mediante `POST /api/courses/<id>/teachers` con body `{"teacher_id": <int>}`, y quitarla mediante `DELETE /api/courses/<id>/teachers/<teacher_id>`. Un curso inexistente MUST responder HTTP 404; un usuario inexistente MUST responder HTTP 404; un usuario cuyo rol no sea Profesor MUST responder HTTP 400; una asignación ya existente MUST responder HTTP 409. En caso de éxito la respuesta MUST reflejar la asignación. Todas las operaciones están restringidas al rol Administrador (401 sin sesión, 403 con otro rol).

#### Scenario: Asignación exitosa de profesor
- **GIVEN** que existe un curso y una cuenta con rol Profesor no asignada aún
- **WHEN** el Administrador envía `POST /api/courses/<id>/teachers` con ese `teacher_id`
- **THEN** el sistema responde con éxito y el profesor queda asignado al curso

#### Scenario: Usuario sin rol Profesor
- **GIVEN** que existe un curso y una cuenta con rol Estudiante
- **WHEN** el Administrador intenta asignarla como profesora del curso
- **THEN** el sistema responde HTTP 400 y no realiza la asignación

#### Scenario: Asignación duplicada
- **GIVEN** que una cuenta ya está asignada como profesora de un curso
- **WHEN** el Administrador intenta asignarla otra vez al mismo curso
- **THEN** el sistema responde HTTP 409 y no duplica la asignación

#### Scenario: Curso o profesor inexistente
- **WHEN** el Administrador intenta asignar un profesor a un curso inexistente o una cuenta inexistente
- **THEN** el sistema responde HTTP 404 y no realiza la asignación

### Requirement: Consulta y remoción de profesores de un curso

El sistema SHALL permitir al Administrador listar los profesores asignados a un curso mediante `GET /api/courses/<id>/teachers` y quitar una asignación mediante `DELETE /api/courses/<id>/teachers/<teacher_id>`. Listar un curso inexistente MUST responder HTTP 404. Quitar una asignación inexistente MUST responder HTTP 404. En caso de éxito la operación MUST dejar la asignación ausente.

#### Scenario: Listado de profesores de un curso
- **GIVEN** que un curso tiene uno o más profesores asignados
- **WHEN** el Administrador envía `GET /api/courses/<id>/teachers`
- **THEN** el sistema responde HTTP 200 con las cuentas de los profesores asignados

#### Scenario: Remoción exitosa
- **GIVEN** que una cuenta está asignada como profesora de un curso
- **WHEN** el Administrador envía `DELETE /api/courses/<id>/teachers/<teacher_id>`
- **THEN** el sistema responde con éxito y la asignación deja de existir

#### Scenario: Remoción de asignación inexistente
- **WHEN** el Administrador intenta quitar una asignación que no existe
- **THEN** el sistema responde HTTP 404
