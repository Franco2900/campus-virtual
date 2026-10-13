# Spec Delta

## MODIFIED Requirements

### Requirement: Alcance de la gestión de tareas

El sistema SHALL restringir las operaciones de gestión de tareas (creación, consulta individual, modificación y activación/desactivación) al rol Profesor. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Profesor MUST responder HTTP 403 sin ejecutar la operación, con la única excepción del listado `GET /api/courses/<id>/tasks`, que es role-aware y se define en el requisito «Consulta de tareas de un curso». Un Profesor MUST poder operar únicamente sobre los cursos en los que está asignado; ante un curso existente en el que no trabaja el sistema MUST responder HTTP 403 sin ejecutar la operación. Ante un curso inexistente el sistema MUST responder HTTP 404.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request a los endpoints de gestión de tareas
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol no Profesor
- **GIVEN** que un usuario con rol Estudiante o Administrador tiene sesión activa
- **WHEN** envía un request de creación, consulta individual, modificación o cambio de estado de tareas
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

#### Scenario: Profesor sobre un curso en el que no trabaja
- **GIVEN** que un Profesor tiene sesión activa y que existe un curso en el que no está asignado
- **WHEN** envía un request de gestión de tareas sobre ese curso
- **THEN** el sistema responde HTTP 403 y no ejecuta la operación

#### Scenario: Curso inexistente
- **WHEN** el Profesor envía un request de gestión de tareas sobre un curso que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Consulta de tareas de un curso

El sistema SHALL permitir listar las tareas de un curso mediante `GET /api/courses/<id>/tasks`, con comportamiento según el rol del usuario autenticado. Para el Profesor, la respuesta MUST incluir todas las tareas del curso, activas e inactivas, con su identificador, título, descripción, fecha límite y estado; sobre un curso en el que no trabaja el sistema MUST responder HTTP 403 y ante un curso inexistente HTTP 404. Para el Estudiante, la respuesta MUST incluir únicamente las tareas disponibles (activas y con la fecha límite vigente) y, en cada una, la entrega propia del Estudiante o `null` si no la realizó; un Estudiante sin inscripción activa en el curso MUST recibir HTTP 403. El listado de un curso sin tareas aplicables al rol MUST responder HTTP 200 con una lista vacía.

#### Scenario: Listado de tareas del curso
- **GIVEN** que existe un curso activo o inactivo, asignado al Profesor, con tareas activas e inactivas
- **WHEN** el Profesor envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 200 con todas las tareas del curso, incluyendo su estado

#### Scenario: Curso sin tareas
- **GIVEN** que existe un curso asignado al Profesor sin tareas registradas
- **WHEN** el Profesor envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 200 con una lista vacía

#### Scenario: Listado de tareas disponibles para el Estudiante
- **GIVEN** que un Estudiante inscripto accede a un curso con tareas activas, tareas inactivas y tareas vencidas, y tiene entrega en algunas
- **WHEN** el Estudiante envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 200 con únicamente las tareas disponibles y, en cada una, su entrega propia o `null`

#### Scenario: Estudiante sin inscripción en el curso
- **GIVEN** que un Estudiante tiene sesión activa y no tiene inscripción activa en el curso
- **WHEN** el Estudiante envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 403 y no devuelve las tareas

#### Scenario: Curso sin tareas disponibles para el Estudiante
- **GIVEN** que un Estudiante inscripto accede a un curso cuyas tareas están todas inactivas o vencidas
- **WHEN** el Estudiante envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 200 con una lista vacía

#### Scenario: Curso inexistente para el Estudiante
- **WHEN** el Estudiante envía `GET /api/courses/<id>/tasks` con un curso que no existe
- **THEN** el sistema responde HTTP 404
