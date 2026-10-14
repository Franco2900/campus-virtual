# grading-management Specification

## Purpose
Permitir al Profesor listar las entregas de una tarea de sus cursos y corregirlas asignando una calificación (1..10) con retroalimentación opcional, derivando automáticamente el estado aprobado/desaprobado (nota >= 6) sin generar notificaciones por correo.

## Requirements

### Requirement: Listado de entregas para corrección
El sistema SHALL permitir al Profesor listar las entregas de una tarea mediante `GET /api/courses/<id>/tasks/<task_id>/submissions`. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Profesor MUST responder HTTP 403 sin ejecutar la operación. El Profesor MUST poder operar únicamente sobre cursos en los que está asignado; ante un curso existente en el que no trabaja el sistema MUST responder HTTP 403. Ante un curso inexistente el sistema MUST responder HTTP 404. La tarea MUST pertenecer al curso indicado; si no existe o pertenece a otro curso, el sistema MUST responder HTTP 404. En caso de éxito MUST responder HTTP 200 con la lista de entregas, incluyendo para cada una: identificación de la entrega, datos del estudiante (nombre y email), contenido y links, estado de corrección (`grade` nulo o con valor), `grade`, `feedback` y `graded_at` cuando esté corregida.

#### Scenario: Profesor asignado lista entregas de tarea existente
- **WHEN** un Profesor autenticado solicita listar entregas de una tarea que pertenece a un curso en el que está asignado
- **THEN** el sistema retorna HTTP 200
- **AND** retorna la lista de entregas de esa tarea con datos del estudiante y estado de corrección

#### Scenario: Profesor no asignado al curso
- **WHEN** un Profesor autenticado solicita listar entregas de una tarea de un curso en el que no está asignado
- **THEN** el sistema retorna HTTP 403
- **AND** no lista las entregas

#### Scenario: Rol no autorizado intenta listar
- **WHEN** un usuario autenticado con rol Estudiante solicita listar entregas de una tarea
- **THEN** el sistema retorna HTTP 403
- **AND** no lista las entregas

#### Scenario: Tarea no pertenece al curso
- **WHEN** un Profesor asignado al curso solicita listar entregas de una tarea que pertenece a otro curso
- **THEN** el sistema retorna HTTP 404
- **AND** no lista las entregas

### Requirement: Corregir o modificar corrección
El sistema SHALL permitir al Profesor corregir una entrega o modificar una corrección existente mediante `PUT /api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade`. El cuerpo de la solicitud MUST incluir `grade` (entero) y MAY incluir `feedback` (texto). `grade` MUST estar entre 1 y 10 inclusive (valores enteros). `feedback`, si está presente, MUST tener como máximo 5000 caracteres; si excede ese límite el sistema MUST responder HTTP 400. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado cuyo rol no sea Profesor MUST responder HTTP 403. El Profesor MUST operar únicamente sobre cursos en los que está asignado (HTTP 403 en caso contrario). Ante curso inexistente el sistema MUST responder HTTP 404. La tarea MUST pertenecer al curso indicado (HTTP 404 en caso contrario). La entrega del estudiante (`student_id`) MUST existir para esa tarea y ese estudiante; si no existe, el sistema MUST responder HTTP 404. La corrección MUST ser posible aunque la inscripción del estudiante haya sido desactivada luego de entregar: la precondición del caso de uso es únicamente que exista la entrega. Ante datos inválidos (rango de calificación incorrecto, tipo incorrecto) el sistema MUST responder HTTP 400 y MUST NOT modificar la corrección. En caso de éxito MUST responder HTTP 200 con la entrega actualizada incluyendo `grade`, `feedback`, `graded_at` y el estado de corrección. La promoción automático de aprobado/desaprobado se deriva de la calificación: aprobado cuando `grade >= 6`, desaprobado cuando `1 <= grade <= 5`. La corrección no genera notificaciones automáticas por correo electrónico.

#### Scenario: Profesor asignado corrige entrega existente
- **WHEN** un Profesor asignado al curso envía `PUT /api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade` con `grade` entre 1 y 10
- **THEN** el sistema retorna HTTP 200
- **AND** guarda `grade`, `feedback` y `graded_at`
- **AND** la entrega refleja el estado corregido

#### Scenario: Profesor asignado modifica corrección existente (A1)
- **WHEN** un Profesor asignado al curso modifica una entrega ya corregida cambiando `grade` o `feedback`
- **THEN** el sistema retorna HTTP 200
- **AND** actualiza la corrección con los nuevos valores
- **AND** actualiza `graded_at` según corresponda

#### Scenario: Calificación fuera de rango
- **WHEN** un Profesor asignado envía `grade` igual a 0 o mayor a 10
- **THEN** el sistema retorna HTTP 400
- **AND** no guarda la corrección

#### Scenario: Calificación no entera o tipo incorrecto
- **WHEN** un Profesor asignado envía `grade` con tipo incorrecto (no entero)
- **THEN** el sistema retorna HTTP 400
- **AND** no guarda la corrección

#### Scenario: Profesor no asignado al curso
- **WHEN** un Profesor no asignado al curso intenta corregir una entrega
- **THEN** el sistema retorna HTTP 403
- **AND** no guarda la corrección

#### Scenario: Rol no autorizado intenta corregir
- **WHEN** un Estudiante intenta corregir una entrega
- **THEN** el sistema retorna HTTP 403
- **AND** no guarda la corrección

#### Scenario: Entrega inexistente para ese estudiante/tarea
- **WHEN** un Profesor asignado intenta corregir una entrega que no existe
- **THEN** el sistema retorna HTTP 404
- **AND** no guarda la corrección

#### Scenario: Tarea no pertenece al curso
- **WHEN** un Profesor asignado intenta corregir una entrega de una tarea que pertenece a otro curso
- **THEN** el sistema retorna HTTP 404
- **AND** no guarda la corrección

#### Scenario: Calificación >= 6 deriva aprobado
- **WHEN** el Profesor asigna una calificación >= 6
- **THEN** la entrega corregida se considera aprobada según la regla de derivación
- **AND** el sistema conserva la calificación numérica

#### Scenario: Calificación entre 1 y 5 deriva desaprobado
- **WHEN** el Profesor asigna una calificación entre 1 y 5
- **THEN** la entrega corregida se considera desaprobada según la regla de derivación
- **AND** el sistema conserva la calificación numérica
