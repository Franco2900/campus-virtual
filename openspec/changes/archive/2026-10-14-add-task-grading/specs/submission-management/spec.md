# Spec Delta

## MODIFIED Requirements

### Requirement: Modificación de la entrega propia

El sistema SHALL permitir al Estudiante modificar su entrega mediante `PUT /api/courses/<id>/tasks/<task_id>/submission`, reemplazando `content` y `links`. Las mismas validaciones de contenido que en la creación MUST aplicarse (HTTP 400 en caso contrario). La modificación MUST permitirse únicamente mientras la tarea esté disponible (HTTP 409 en caso contrario). Si la entrega ya fue corregida (su `grade` no es nulo), el sistema MUST responder HTTP 409 y MUST NOT modificar la entrega. Si no existe una entrega propia para esa tarea el sistema MUST responder HTTP 404. En caso de éxito MUST responder HTTP 200 con la entrega actualizada.

#### Scenario: Modificación exitosa
- **GIVEN** que el Estudiante tiene una entrega no corregida y la tarea sigue disponible
- **WHEN** el Estudiante envía `PUT` con contenido válido
- **THEN** el sistema responde HTTP 200 con la entrega actualizada

#### Scenario: Modificación sin entrega existente
- **WHEN** el Estudiante envía `PUT` para una tarea sobre la que no tiene entrega
- **THEN** el sistema responde HTTP 404

#### Scenario: Modificación con la tarea no disponible
- **GIVEN** que el Estudiante tiene una entrega y la tarea está inactiva o el plazo venció
- **WHEN** el Estudiante envía `PUT`
- **THEN** el sistema responde HTTP 409 y no modifica la entrega

#### Scenario: Modificación con contenido inválido
- **WHEN** el Estudiante envía `PUT` sin `content` y sin `links`, o con ambos vacíos
- **THEN** el sistema responde HTTP 400 y no modifica la entrega

#### Scenario: Modificación de una entrega ya corregida
- **GIVEN** que el Estudiante tiene una entrega que fue corregida por el Profesor (tiene `grade`)
- **WHEN** el Estudiante envía `PUT` para modificarla
- **THEN** el sistema responde HTTP 409 y no modifica la entrega

### Requirement: Eliminación de la entrega propia

El sistema SHALL permitir al Estudiante eliminar su entrega mediante `DELETE /api/courses/<id>/tasks/<task_id>/submission`. La eliminación MUST ser física y la interfaz del cliente MUST solicitar confirmación antes de ejecutarla. La eliminación MUST permitirse únicamente mientras la tarea esté disponible (HTTP 409 en caso contrario). Si la entrega ya fue corregida (su `grade` no es nulo), el sistema MUST responder HTTP 409 y MUST NOT eliminar la entrega. Si no existe una entrega propia para esa tarea el sistema MUST responder HTTP 404. En caso de éxito MUST responder HTTP 200 y la entrega MUST dejar de existir, habilitando al Estudiante a entregar nuevamente dentro del plazo.

#### Scenario: Eliminación exitosa
- **GIVEN** que el Estudiante tiene una entrega no corregida y la tarea sigue disponible
- **WHEN** el Estudiante envía `DELETE`
- **THEN** el sistema responde HTTP 200 y la entrega deja de existir

#### Scenario: Eliminación sin entrega existente
- **WHEN** el Estudiante envía `DELETE` para una tarea sobre la que no tiene entrega
- **THEN** el sistema responde HTTP 404

#### Scenario: Eliminación con la tarea no disponible
- **GIVEN** que el Estudiante tiene una entrega y la tarea está inactiva o el plazo venció
- **WHEN** el Estudiante envía `DELETE`
- **THEN** el sistema responde HTTP 409 y no elimina la entrega

#### Scenario: Re-entrega tras eliminar
- **GIVEN** que el Estudiante eliminó su entrega dentro del plazo
- **WHEN** el Estudiante envía `POST` nuevamente para la misma tarea
- **THEN** el sistema crea una nueva entrega

#### Scenario: Eliminación de una entrega ya corregida
- **GIVEN** que el Estudiante tiene una entrega que fue corregida por el Profesor (tiene `grade`)
- **WHEN** el Estudiante envía `DELETE` para eliminarla
- **THEN** el sistema responde HTTP 409 y no elimina la entrega
