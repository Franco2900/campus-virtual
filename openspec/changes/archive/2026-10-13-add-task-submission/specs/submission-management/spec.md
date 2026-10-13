# Spec Delta

## Purpose

Permitir al Estudiante entregar, modificar y eliminar su trabajo —texto y links— para las tareas de los cursos en los que está inscripto, respetando la disponibilidad de la tarea y su fecha límite.

## ADDED Requirements

### Requirement: Alcance de la entrega del Estudiante

El sistema SHALL restringir las operaciones de entrega (crear, modificar y eliminar la entrega propia) al rol Estudiante. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Estudiante (Profesor o Administrador) MUST responder HTTP 403 sin ejecutar la operación. El Estudiante MUST poder operar únicamente sobre cursos en los que tiene una inscripción activa; ante un curso en el que no está inscripto el sistema MUST responder HTTP 403 sin ejecutar la operación. Ante un curso inexistente el sistema MUST responder HTTP 404. Ante una tarea inexistente o que pertenece a otro curso el sistema MUST responder HTTP 404.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request a los endpoints de entrega
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol no Estudiante
- **GIVEN** que un usuario con rol Profesor o Administrador tiene sesión activa
- **WHEN** envía cualquier request a los endpoints de entrega
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

#### Scenario: Estudiante sin inscripción en el curso
- **GIVEN** que un Estudiante tiene sesión activa y no tiene inscripción activa en un curso existente
- **WHEN** envía un request de entrega sobre ese curso
- **THEN** el sistema responde HTTP 403 y no ejecuta la operación

#### Scenario: Curso inexistente
- **WHEN** el Estudiante envía un request de entrega sobre un curso que no existe
- **THEN** el sistema responde HTTP 404

#### Scenario: Tarea inexistente o de otro curso
- **WHEN** el Estudiante envía un request de entrega para una tarea que no existe o que pertenece a un curso distinto al indicado en la ruta
- **THEN** el sistema responde HTTP 404

### Requirement: Disponibilidad y plazo de la tarea

El sistema SHALL considerar una tarea disponible para el Estudiante cuando está activa y su fecha límite (`due_date`) no venció. La comparación de la fecha límite MUST realizarse en UTC normalizado: una `due_date` devuelta por SQLite sin información de zona horaria MUST interpretarse como UTC y MUST compararse contra el instante actual en UTC. Crear, modificar o eliminar una entrega MUST permitirse únicamente mientras la tarea esté disponible; si la tarea está inactiva o el plazo venció, el sistema MUST responder HTTP 409 y MUST NOT ejecutar la operación.

#### Scenario: Tarea disponible
- **GIVEN** que existe una tarea activa con fecha límite futura en un curso donde el Estudiante está inscripto
- **WHEN** el Estudiante opera sobre su entrega
- **THEN** el sistema permite la operación

#### Scenario: Tarea inactiva
- **GIVEN** que existe una tarea inactiva en un curso donde el Estudiante está inscripto
- **WHEN** el Estudiante intenta crear, modificar o eliminar una entrega de esa tarea
- **THEN** el sistema responde HTTP 409 y no ejecuta la operación

#### Scenario: Plazo vencido
- **GIVEN** que existe una tarea activa cuya fecha límite ya pasó
- **WHEN** el Estudiante intenta crear, modificar o eliminar una entrega de esa tarea
- **THEN** el sistema responde HTTP 409 y no ejecuta la operación

#### Scenario: Normalización de zona horaria
- **GIVEN** que una tarea tiene una fecha límite registrada en UTC
- **WHEN** el sistema evalúa el plazo
- **THEN** la comparación se realiza contra el instante UTC normalizado, sin desfases por la ausencia de offset en SQLite

### Requirement: Creación de la entrega propia

El sistema SHALL permitir al Estudiante crear su entrega para una tarea disponible mediante `POST /api/courses/<id>/tasks/<task_id>/submission`. El cuerpo MAY incluir `content` (texto) y `links` (lista de enlaces); MUST incluir al menos uno de los dos con contenido no vacío; en caso contrario el sistema MUST responder HTTP 400 y MUST NOT crear la entrega. La entrega MUST asociarse al par (tarea, estudiante) y MUST ser única por par. Si ya existe una entrega para ese par, el sistema MUST responder HTTP 409 y MUST NOT duplicarla. En caso de éxito MUST responder HTTP 201 con la entrega creada.

#### Scenario: Entrega exitosa con texto
- **GIVEN** que existe una tarea disponible en un curso donde el Estudiante está inscripto y no tiene entrega previa
- **WHEN** el Estudiante envía `POST` con `content` no vacío
- **THEN** el sistema responde HTTP 201 con la entrega creada asociada al par (tarea, estudiante)

#### Scenario: Entrega exitosa con links
- **GIVEN** que existe una tarea disponible en un curso donde el Estudiante está inscripto y no tiene entrega previa
- **WHEN** el Estudiante envía `POST` con `content` vacío y una lista de `links` no vacía
- **THEN** el sistema responde HTTP 201 con la entrega creada

#### Scenario: Cuerpo sin contenido
- **WHEN** el Estudiante envía `POST` sin `content` y sin `links`, o con ambos vacíos
- **THEN** el sistema responde HTTP 400 y no crea la entrega

#### Scenario: Entrega duplicada
- **GIVEN** que el Estudiante ya tiene una entrega para una tarea
- **WHEN** el Estudiante envía `POST` para la misma tarea
- **THEN** el sistema responde HTTP 409 y no duplica la entrega

#### Scenario: Links con formato inválido
- **WHEN** el Estudiante envía `POST` con `links` que no es una lista de textos o cuyos elementos superan el largo permitido
- **THEN** el sistema responde HTTP 400 y no crea la entrega

### Requirement: Modificación de la entrega propia

El sistema SHALL permitir al Estudiante modificar su entrega mediante `PUT /api/courses/<id>/tasks/<task_id>/submission`, reemplazando `content` y `links`. Las mismas validaciones de contenido que en la creación MUST aplicarse (HTTP 400 en caso contrario). La modificación MUST permitirse únicamente mientras la tarea esté disponible (HTTP 409 en caso contrario). Si no existe una entrega propia para esa tarea el sistema MUST responder HTTP 404. En caso de éxito MUST responder HTTP 200 con la entrega actualizada.

#### Scenario: Modificación exitosa
- **GIVEN** que el Estudiante tiene una entrega y la tarea sigue disponible
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

### Requirement: Eliminación de la entrega propia

El sistema SHALL permitir al Estudiante eliminar su entrega mediante `DELETE /api/courses/<id>/tasks/<task_id>/submission`. La eliminación MUST ser física y la interfaz del cliente MUST solicitar confirmación antes de ejecutarla. La eliminación MUST permitirse únicamente mientras la tarea esté disponible (HTTP 409 en caso contrario). Si no existe una entrega propia para esa tarea el sistema MUST responder HTTP 404. En caso de éxito MUST responder HTTP 200 y la entrega MUST dejar de existir, habilitando al Estudiante a entregar nuevamente dentro del plazo.

#### Scenario: Eliminación exitosa
- **GIVEN** que el Estudiante tiene una entrega y la tarea sigue disponible
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

### Requirement: Ausencia de notificaciones por la entrega

Las operaciones de entrega (creación, modificación y eliminación) MUST NOT generar notificaciones automáticas por correo electrónico. Las operaciones MUST limitarse a persistir y devolver la entrega.

#### Scenario: Entrega sin notificación
- **GIVEN** que el Estudiante crea, modifica o elimina una entrega
- **WHEN** la operación finaliza con éxito
- **THEN** el sistema no envía ningún correo electrónico a los involucrados
