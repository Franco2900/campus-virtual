# Spec Delta

## Purpose

Permitir al Profesor gestionar las tareas de los cursos en los que trabaja dentro del Campus Virtual: consultar, crear, modificar y activar/desactivar tareas, respetando el alcance por curso asignado y el estado activo/inactivo de cada tarea.

## ADDED Requirements

### Requirement: Alcance de la gestión de tareas

El sistema SHALL restringir la gestión de tareas al rol Profesor. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Profesor (Estudiante o Administrador) MUST responder HTTP 403 sin ejecutar la operación. Un Profesor MUST poder operar únicamente sobre los cursos en los que está asignado; ante un curso existente en el que no trabaja el sistema MUST responder HTTP 403 sin ejecutar la operación. Ante un curso inexistente el sistema MUST responder HTTP 404.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request a los endpoints de gestión de tareas
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol no Profesor
- **GIVEN** que un usuario con rol Estudiante o Administrador tiene sesión activa
- **WHEN** envía cualquier request a los endpoints de gestión de tareas
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

#### Scenario: Profesor sobre un curso en el que no trabaja
- **GIVEN** que un Profesor tiene sesión activa y que existe un curso en el que no está asignado
- **WHEN** envía un request de gestión de tareas sobre ese curso
- **THEN** el sistema responde HTTP 403 y no ejecuta la operación

#### Scenario: Curso inexistente
- **WHEN** el Profesor envía un request de gestión de tareas sobre un curso que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Consulta de tareas de un curso

El sistema SHALL permitir listar las tareas de un curso mediante `GET /api/courses/<id>/tasks`. La respuesta MUST incluir todas las tareas del curso, tanto activas como inactivas, con su identificador, título, descripción, fecha límite y estado. El listado de un curso sin tareas MUST responder HTTP 200 con una lista vacía. Consultar un curso inexistente MUST responder HTTP 404 y un curso sobre el que el Profesor no trabaja MUST responder HTTP 403.

#### Scenario: Listado de tareas del curso
- **GIVEN** que existe un curso activo o inactivo, asignado al Profesor, con tareas activas e inactivas
- **WHEN** el Profesor envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 200 con todas las tareas del curso, incluyendo su estado

#### Scenario: Curso sin tareas
- **GIVEN** que existe un curso asignado al Profesor sin tareas registradas
- **WHEN** el Profesor envía `GET /api/courses/<id>/tasks`
- **THEN** el sistema responde HTTP 200 con una lista vacía

### Requirement: Consulta de una tarea

El sistema SHALL permitir consultar una tarea puntual mediante `GET /api/courses/<id>/tasks/<task_id>`. La tarea MUST pertenecer al curso indicado; si no existe o pertenece a otro curso, el sistema MUST responder HTTP 404. En caso de éxito MUST responder HTTP 200 con los datos de la tarea.

#### Scenario: Consulta exitosa
- **GIVEN** que existe una tarea en un curso asignado al Profesor
- **WHEN** el Profesor envía `GET /api/courses/<id>/tasks/<task_id>` de esa tarea
- **THEN** el sistema responde HTTP 200 con los datos de la tarea

#### Scenario: Tarea inexistente o de otro curso
- **WHEN** el Profesor consulta una tarea que no existe o que pertenece a un curso distinto al indicado en la ruta
- **THEN** el sistema responde HTTP 404

### Requirement: Creación de una tarea

El sistema SHALL permitir crear una tarea en un curso mediante `POST /api/courses/<id>/tasks`. El cuerpo MUST incluir `title` (obligatorio, no vacío) y `due_date` (obligatoria, fecha válida); `description` MAY estar presente y por defecto es vacía. La tarea MUST crearse asociada al curso y en estado activo. El curso MUST estar activo; operar sobre un curso inactivo MUST responder HTTP 409. Ante datos inválidos o faltantes el sistema MUST responder HTTP 400 sin crear la tarea. En caso de éxito MUST responder HTTP 201 con la tarea creada.

#### Scenario: Creación exitosa
- **GIVEN** que existe un curso activo asignado al Profesor
- **WHEN** el Profesor envía `POST /api/courses/<id>/tasks` con un `title` no vacío y una `due_date` válida
- **THEN** el sistema responde HTTP 201 con la tarea creada en estado activo y asociada al curso

#### Scenario: Creación con descripción opcional omitida
- **GIVEN** que existe un curso activo asignado al Profesor
- **WHEN** el Profesor crea una tarea sin enviar `description`
- **THEN** el sistema responde HTTP 201 y la tarea queda con descripción vacía

#### Scenario: Título faltante o vacío
- **GIVEN** que existe un curso activo asignado al Profesor
- **WHEN** el Profesor envía `POST /api/courses/<id>/tasks` sin `title` o con `title` vacío
- **THEN** el sistema responde HTTP 400 y no crea la tarea

#### Scenario: Fecha límite faltante o inválida
- **GIVEN** que existe un curso activo asignado al Profesor
- **WHEN** el Profesor envía `POST /api/courses/<id>/tasks` sin `due_date` o con un valor que no es una fecha válida
- **THEN** el sistema responde HTTP 400 y no crea la tarea

#### Scenario: Creación en un curso inactivo
- **GIVEN** que existe un curso inactivo asignado al Profesor
- **WHEN** el Profesor intenta crear una tarea en ese curso
- **THEN** el sistema responde HTTP 409 y no crea la tarea

### Requirement: Modificación de una tarea

El sistema SHALL permitir modificar los datos de una tarea existente mediante `PUT /api/courses/<id>/tasks/<task_id>`, incluyendo la fecha límite. El cuerpo MUST incluir `title` y `due_date` válidos; `description` MAY estar presente. La tarea MUST pertenecer al curso indicado (HTTP 404 en caso contrario). El curso MUST estar activo; operar sobre un curso inactivo MUST responder HTTP 409. Ante datos inválidos el sistema MUST responder HTTP 400 y MUST NOT modificar la tarea. En caso de éxito MUST responder HTTP 200 con la tarea actualizada.

#### Scenario: Modificación exitosa de datos
- **GIVEN** que existe una tarea activa en un curso activo asignado al Profesor
- **WHEN** el Profesor envía `PUT /api/courses/<id>/tasks/<task_id>` con un nuevo `title` y `description`
- **THEN** el sistema responde HTTP 200 con los datos actualizados

#### Scenario: Modificación de la fecha límite
- **GIVEN** que existe una tarea activa en un curso activo asignado al Profesor
- **WHEN** el Profesor envía `PUT /api/courses/<id>/tasks/<task_id>` con una nueva `due_date` válida
- **THEN** el sistema responde HTTP 200 y la fecha límite queda actualizada

#### Scenario: Modificación con datos inválidos
- **WHEN** el Profesor envía `PUT /api/courses/<id>/tasks/<task_id>` con `title` vacío o `due_date` inválida o faltante
- **THEN** el sistema responde HTTP 400 y no modifica la tarea

#### Scenario: Modificación de una tarea inexistente
- **WHEN** el Profesor envía `PUT /api/courses/<id>/tasks/<task_id>` para una tarea que no existe en ese curso
- **THEN** el sistema responde HTTP 404

### Requirement: Activación y desactivación de una tarea

El sistema SHALL permitir cambiar el estado de una tarea mediante `PATCH /api/courses/<id>/tasks/<task_id>` con body `{"active": <bool>}`. El campo `active` MUST ser booleano (HTTP 400 en caso contrario). La tarea MUST pertenecer al curso indicado (HTTP 404 en caso contrario). El cambio de estado MUST permitirse aunque el curso esté inactivo. En caso de éxito MUST responder HTTP 200 reflejando el nuevo estado. Una tarea inactiva MUST NOT considerarse disponible para los estudiantes.

#### Scenario: Desactivación de una tarea
- **GIVEN** que existe una tarea activa
- **WHEN** el Profesor envía `PATCH /api/courses/<id>/tasks/<task_id>` indicando `active: false`
- **THEN** el sistema responde HTTP 200 y la tarea queda inactiva sin eliminarse

#### Scenario: Reactivación de una tarea
- **GIVEN** que existe una tarea inactiva
- **WHEN** el Profesor envía `PATCH /api/courses/<id>/tasks/<task_id>` indicando `active: true`
- **THEN** el sistema responde HTTP 200 y la tarea vuelve a estar disponible

#### Scenario: Valor inválido de active
- **WHEN** el Profesor envía `PATCH /api/courses/<id>/tasks/<task_id>` sin `active` o con un valor no booleano
- **THEN** el sistema responde HTTP 400 y no modifica la tarea

#### Scenario: Tarea inexistente al cambiar estado
- **WHEN** el Profesor envía `PATCH /api/courses/<id>/tasks/<task_id>` para una tarea que no existe en ese curso
- **THEN** el sistema responde HTTP 404

### Requirement: Ausencia de notificaciones por la gestión de tareas

La gestión de tareas MUST NOT generar notificaciones automáticas por correo electrónico. Las operaciones de creación, consulta, modificación y cambio de estado MUST limitarse a persistir y devolver la tarea.

#### Scenario: Modificación sin notificación
- **GIVEN** que se crea o modifica una tarea
- **WHEN** la operación finaliza con éxito
- **THEN** el sistema no envía ningún correo electrónico a los involucrados
