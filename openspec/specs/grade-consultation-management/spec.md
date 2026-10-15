# grade-consultation-management Specification

## Purpose
Permitir que el Estudiante consulte sus propias calificaciones —detalle por tarea con nota y retroalimentación, más el promedio del curso— y que el Profesor consulte las calificaciones de los estudiantes de sus cursos en una matriz estudiante × tarea con el promedio del curso, aplicando el promedio simple sobre las tareas activas y sin generar notificaciones por correo.

## Requirements

### Requirement: Consulta de calificaciones por el Estudiante

El sistema SHALL permitir al Estudiante consultar sus propias calificaciones en un curso mediante `GET /api/courses/<id>/grades`. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Profesor ni Estudiante (por ejemplo Administrador) MUST responder HTTP 403 sin ejecutar la consulta. Ante un curso inexistente el sistema MUST responder HTTP 404. El Estudiante MUST tener una inscripción activa en el curso; ante un curso en el que no está inscripto el sistema MUST responder HTTP 403 sin ejecutar la consulta. En caso de éxito el sistema MUST responder HTTP 200 con el detalle de sus propias calificaciones y el promedio del curso. El Estudiante MUST poder consultar únicamente sus propias calificaciones; el sistema MUST NOT exponer calificaciones ni datos de otros estudiantes en esta vista.

#### Scenario: Estudiante inscripto consulta sus calificaciones
- **GIVEN** que un Estudiante tiene sesión activa y una inscripción activa en un curso existente
- **WHEN** envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 200 con el detalle de sus calificaciones y el promedio del curso

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Rol no autorizado
- **GIVEN** que un usuario con rol Administrador tiene sesión activa
- **WHEN** envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 403 y no ejecuta la consulta

#### Scenario: Estudiante sin inscripción activa en el curso
- **GIVEN** que un Estudiante tiene sesión activa y no tiene inscripción activa en un curso existente
- **WHEN** envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 403 y no devuelve calificaciones

#### Scenario: Curso inexistente para el Estudiante
- **WHEN** el Estudiante envía `GET /api/courses/<id>/grades` con un curso que no existe
- **THEN** el sistema responde HTTP 404

#### Scenario: Aislamiento de las calificaciones del Estudiante
- **GIVEN** que un curso tiene varios estudiantes con calificaciones
- **WHEN** un Estudiante consulta `GET /api/courses/<id>/grades`
- **THEN** la respuesta contiene únicamente las calificaciones del Estudiante solicitante

### Requirement: Consulta de calificaciones por el Profesor

El sistema SHALL permitir al Profesor consultar las calificaciones de los estudiantes de sus cursos mediante `GET /api/courses/<id>/grades`. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Profesor ni Estudiante (por ejemplo Administrador) MUST responder HTTP 403. El Profesor MUST poder consultar únicamente los cursos en los que está asignado; ante un curso en el que no trabaja el sistema MUST responder HTTP 403 sin ejecutar la consulta. Ante un curso inexistente el sistema MUST responder HTTP 404. En caso de éxito el sistema MUST responder HTTP 200 con la matriz de estudiantes × tareas de los estudiantes con inscripción activa en el curso y el promedio del curso. El Profesor MUST poder consultar únicamente las calificaciones de los estudiantes de sus cursos.

#### Scenario: Profesor asignado consulta la matriz de calificaciones
- **GIVEN** que un Profesor tiene sesión activa y está asignado a un curso con estudiantes inscriptos y tareas
- **WHEN** envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 200 con la matriz de estudiantes × tareas y el promedio del curso

#### Scenario: Profesor no asignado al curso
- **GIVEN** que un Profesor tiene sesión activa y existe un curso en el que no está asignado
- **WHEN** envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 403 y no devuelve calificaciones

#### Scenario: Curso inexistente para el Profesor
- **WHEN** el Profesor envía `GET /api/courses/<id>/grades` con un curso que no existe
- **THEN** el sistema responde HTTP 404

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

### Requirement: Detalle de calificaciones del Estudiante

El sistema SHALL devolver, en la vista del Estudiante, el detalle por tarea y el promedio del curso. El detalle MUST incluir todas las tareas activas del curso, y por cada una: el identificador y el título de la tarea, la fecha límite, la nota cuando está corregida (o su ausencia), la retroalimentación cuando está corregida y el estado de corrección. El sistema MUST exponer la nota, la retroalimentación y el estado aprobado/desaprobado derivado (`grade >= 6`) al Estudiante cuando la tarea está corregida. Las tareas inactivas del curso MUST NOT incluirse en el detalle.

#### Scenario: Tarea corregida muestra nota y retroalimentación
- **GIVEN** que el Estudiante tiene una entrega corregida con nota y retroalimentación en una tarea activa
- **WHEN** el Estudiante consulta `GET /api/courses/<id>/grades`
- **THEN** el detalle de esa tarea incluye la nota, la retroalimentación y el estado de aprobación

#### Scenario: Tarea sin corregir no muestra nota
- **GIVEN** que el Estudiante tiene una tarea activa cuya entrega aún no fue corregida
- **WHEN** el Estudiante consulta `GET /api/courses/<id>/grades`
- **THEN** el detalle de esa tarea aparece sin nota, indicando que no está corregida

#### Scenario: Tarea vencida sin entrega
- **GIVEN** que existe una tarea activa cuya fecha límite ya venció y el Estudiante no realizó la entrega
- **WHEN** el Estudiante consulta `GET /api/courses/<id>/grades`
- **THEN** el detalle de esa tarea refleja la situación de entrega vencida sin entrega

### Requirement: Matriz de calificaciones del Profesor

El sistema SHALL devolver, en la vista del Profesor, una matriz de estudiantes × tareas y el promedio del curso. La matriz MUST incluir como filas a los estudiantes con inscripción activa en el curso y como columnas las tareas activas del curso. Para cada par (estudiante, tarea) la matriz MUST reflejar la calificación correspondiente según la regla del promedio (nota si la entrega está corregida, 1 si la fecha límite venció sin entrega, o la ausencia de calificación) y MUST incluir el promedio por estudiante. El promedio del curso MUST calcularse sobre los estudiantes inscriptos.

#### Scenario: Matriz con estudiantes y tareas
- **GIVEN** que un curso asignado al Profesor tiene estudiantes inscriptos y tareas activas con algunas entregas corregidas
- **WHEN** el Profesor consulta `GET /api/courses/<id>/grades`
- **THEN** la respuesta incluye una fila por estudiante inscripto y una columna por tarea activa, con la calificación de cada celda y el promedio por estudiante

#### Scenario: Curso sin estudiantes inscriptos
- **GIVEN** que un curso asignado al Profesor no tiene estudiantes con inscripción activa
- **WHEN** el Profesor consulta `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 200 con la matriz sin filas de estudiantes

#### Scenario: Curso sin tareas activas
- **GIVEN** que un curso asignado al Profesor no tiene tareas activas
- **WHEN** el Profesor consulta `GET /api/courses/<id>/grades`
- **THEN** el sistema responde HTTP 200 con la matriz sin columnas de tareas y sin promedio de curso

### Requirement: Regla del promedio simple

El sistema SHALL calcular el promedio como un promedio simple (media aritmética, sin ponderación). El cálculo MUST considerar únicamente las tareas activas del curso. Cada tarea activa MUST aportar al promedio: su nota cuando la entrega está corregida, o el valor 1 cuando la fecha límite (`due_date`) ya venció y no hubo entrega. Las tareas inactivas, las tareas que aún no vencieron y las tareas no corregidas MUST quedar fuera del cálculo. La comparación de la fecha límite MUST realizarse en UTC normalizado. Cuando ninguna tarea aporte un valor al promedio, el promedio MUST devolverse como nulo (no como 0).

#### Scenario: Promedio con tareas corregidas
- **GIVEN** que un Estudiante tiene tareas activas corregidas con notas 8 y 6
- **WHEN** se calcula su promedio
- **THEN** el promedio es la media simple de las notas que aportan al cálculo

#### Scenario: Tarea vencida sin entrega cuenta como 1
- **GIVEN** que una tarea activa venció y el Estudiante no realizó la entrega
- **WHEN** se calcula su promedio
- **THEN** esa tarea aporta el valor 1 al promedio

#### Scenario: Tarea no corregida no se incluye
- **GIVEN** que el Estudiante tiene una entrega en una tarea activa que aún no fue corregida
- **WHEN** se calcula su promedio
- **THEN** esa tarea no aporta ningún valor al promedio

#### Scenario: Tarea inactiva no se incluye
- **GIVEN** que el curso tiene una tarea inactiva con una nota registrada
- **WHEN** se calcula el promedio
- **THEN** esa tarea no aporta al promedio

#### Scenario: Tarea que aún no venció no se incluye
- **GIVEN** que una tarea activa tiene una fecha límite futura
- **WHEN** se calcula el promedio antes de su vencimiento
- **THEN** esa tarea no aporta ningún valor al promedio

#### Scenario: Sin valores que aporten al promedio
- **GIVEN** que ninguna tarea del curso aporta un valor al promedio de un estudiante
- **WHEN** se calcula su promedio
- **THEN** el promedio devuelto es nulo

### Requirement: Ausencia de notificaciones por la consulta de calificaciones

La consulta de calificaciones MUST NOT generar notificaciones automáticas por correo electrónico. La operación MUST limitarse a leer y devolver las calificaciones y el promedio.

#### Scenario: Consulta sin notificación
- **GIVEN** que un Estudiante o un Profesor consulta las calificaciones de un curso
- **WHEN** la consulta finaliza con éxito
- **THEN** el sistema no envía ningún correo electrónico a los involucrados
