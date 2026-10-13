# enrollment-management Specification

## Purpose
Permitir al Administrador y al Profesor gestionar las inscripciones de estudiantes en los cursos del Campus Virtual: consultar el estado de inscripción de cada estudiante, inscribir, modificar (activar/desactivar) y eliminar inscripciones, respetando el alcance por rol sobre los cursos.

## Requirements

### Requirement: Alcance de la gestión de inscripciones

El sistema SHALL restringir la gestión de inscripciones a los roles Administrador y Profesor. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado con rol Estudiante MUST responder HTTP 403 sin ejecutar la operación. Un Profesor MUST poder operar únicamente sobre los cursos en los que está asignado; ante un curso en el que no trabaja el sistema MUST responder HTTP 403 sin ejecutar la operación, incluso si el curso existe.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request a los endpoints de gestión de inscripciones
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol Estudiante
- **GIVEN** que un usuario con rol Estudiante tiene sesión activa
- **WHEN** envía cualquier request a los endpoints de gestión de inscripciones
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

#### Scenario: Profesor sobre un curso en el que no trabaja
- **GIVEN** que un Profesor tiene sesión activa y que existe un curso en el que no está asignado
- **WHEN** envía un request de gestión de inscripciones sobre ese curso
- **THEN** el sistema responde HTTP 403 y no ejecuta la operación

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

### Requirement: Consulta de estudiantes e inscripciones de un curso

El sistema SHALL permitir listar, mediante `GET /api/courses/<id>/students`, los estudiantes del sistema y su estado de inscripción en el curso: cada elemento MUST indicar si el estudiante tiene una inscripción y, de tenerla, su estado (activa o inactiva) y su fecha de inscripción. El listado MUST incluir únicamente cuentas activas con rol Estudiante. Consultar un curso inexistente MUST responder HTTP 404. Consultar un curso sobre el que un Profesor no trabaja MUST responder HTTP 403.

#### Scenario: Listado de estudiantes con su estado
- **GIVEN** que existe un curso y que hay estudiantes inscriptos (activos e inactivos) y estudiantes sin inscripción
- **WHEN** el Administrador o el Profesor asignado envía `GET /api/courses/<id>/students`
- **THEN** el sistema responde HTTP 200 con los estudiantes activos y, para cada uno, su inscripción con estado y fecha cuando existe

#### Scenario: Listado de un curso inexistente
- **WHEN** un Administrador o Profesor envía `GET /api/courses/<id>/students` con un identificador que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Inscripción de estudiantes

El sistema SHALL permitir inscribir un estudiante en un curso mediante `POST /api/courses/<id>/students` con body `{"student_id": <int>}`. La inscripción MUST crearse en estado activa y asociada al par curso+estudiante. El curso MUST existir y estar activo; operar sobre un curso inactivo MUST responder HTTP 409. La cuenta indicada MUST existir (HTTP 404 si no existe), MUST estar activa y MUST tener rol Estudiante (HTTP 400 en caso contrario). Si el estudiante ya tiene una inscripción en el curso (activa o inactiva), el sistema MUST responder HTTP 409 y MUST NOT duplicar el vínculo. En caso de éxito MUST responder HTTP 201 con la inscripción creada.

#### Scenario: Inscripción exitosa
- **GIVEN** que existe un curso activo y una cuenta activa con rol Estudiante sin inscripción en ese curso
- **WHEN** el Administrador o el Profesor asignado envía `POST /api/courses/<id>/students` con ese `student_id`
- **THEN** el sistema responde HTTP 201 y el estudiante queda inscripto con estado activo

#### Scenario: Inscripción duplicada
- **GIVEN** que un estudiante ya tiene una inscripción (activa o inactiva) en un curso
- **WHEN** se intenta inscribir al mismo estudiante en el mismo curso
- **THEN** el sistema responde HTTP 409 y no crea una segunda inscripción

#### Scenario: Cuenta sin rol Estudiante
- **GIVEN** que existe un curso activo y una cuenta activa cuyo rol no es Estudiante
- **WHEN** se intenta inscribir esa cuenta en el curso
- **THEN** el sistema responde HTTP 400 y no crea la inscripción

#### Scenario: Cuenta inactiva
- **GIVEN** que existe un curso activo y una cuenta con rol Estudiante desactivada
- **WHEN** se intenta inscribir esa cuenta en el curso
- **THEN** el sistema responde HTTP 400 y no crea la inscripción

#### Scenario: Curso inactivo
- **GIVEN** que existe un curso inactivo
- **WHEN** se intenta inscribir un estudiante en ese curso
- **THEN** el sistema responde HTTP 409 y no crea la inscripción

#### Scenario: Curso o estudiante inexistente
- **WHEN** se intenta inscribir un estudiante en un curso inexistente o una cuenta inexistente
- **THEN** el sistema responde HTTP 404 y no crea la inscripción

### Requirement: Modificación de una inscripción

El sistema SHALL permitir modificar el estado de una inscripción existente mediante `PATCH /api/courses/<id>/students/<student_id>` con body `{"active": <bool>}`. El campo `active` MUST ser booleano (HTTP 400 en caso contrario). Operar sobre una inscripción inexistente MUST responder HTTP 404. El curso MUST estar activo; operar sobre un curso inactivo MUST responder HTTP 409. En caso de éxito MUST responder HTTP 200 reflejando el nuevo estado. Una inscripción inactiva MUST NOT contarse como estudiante inscripto.

#### Scenario: Desactivación de una inscripción
- **GIVEN** que existe una inscripción activa en un curso activo
- **WHEN** el Administrador o el Profesor asignado envía `PATCH` indicando `active: false`
- **THEN** el sistema responde HTTP 200 y la inscripción queda inactiva sin eliminarse

#### Scenario: Reactivación de una inscripción
- **GIVEN** que existe una inscripción inactiva en un curso activo
- **WHEN** el Administrador o el Profesor asignado envía `PATCH` indicando `active: true`
- **THEN** el sistema responde HTTP 200 y la inscripción vuelve a contarse como inscripto

#### Scenario: Inscripción inexistente
- **WHEN** se envía `PATCH /api/courses/<id>/students/<student_id>` para un par curso+estudiante sin inscripción
- **THEN** el sistema responde HTTP 404 y no modifica nada

#### Scenario: Valor inválido de active
- **WHEN** se envía `PATCH /api/courses/<id>/students/<student_id>` sin `active` o con un valor no booleano
- **THEN** el sistema responde HTTP 400 y no modifica nada

### Requirement: Eliminación de una inscripción

El sistema SHALL permitir eliminar una inscripción mediante `DELETE /api/courses/<id>/students/<student_id>`, removiendo el vínculo de forma física. Eliminar una inscripción inexistente MUST responder HTTP 404. La operación MUST permitirse aunque el curso esté inactivo. En caso de éxito MUST responder HTTP 200 y el estudiante MUST dejar de figurar como inscripto, quedando habilitado a ser inscripto nuevamente.

#### Scenario: Eliminación exitosa
- **GIVEN** que existe una inscripción en un curso
- **WHEN** el Administrador o el Profesor asignado envía `DELETE /api/courses/<id>/students/<student_id>`
- **THEN** el sistema responde HTTP 200 y la inscripción deja de existir

#### Scenario: Eliminación de inscripción inexistente
- **WHEN** se intenta eliminar una inscripción que no existe
- **THEN** el sistema responde HTTP 404

#### Scenario: Reinscripción posterior a la eliminación
- **GIVEN** que una inscripción fue eliminada
- **WHEN** se inscribe nuevamente al mismo estudiante en el mismo curso
- **THEN** el sistema permite la operación y crea una nueva inscripción activa

### Requirement: Ausencia de notificaciones por la gestión de inscripciones

La gestión de inscripciones MUST NOT generar notificaciones automáticas por correo electrónico. Las operaciones MUST limitarse a persistir y devolver el estado de la inscripción.

#### Scenario: Inscripción sin notificación
- **GIVEN** que se registra, modifica o elimina una inscripción
- **WHEN** la operación finaliza con éxito
- **THEN** el sistema no envía ningún correo electrónico a los involucrados
