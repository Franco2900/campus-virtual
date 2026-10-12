# Spec Delta

## MODIFIED Requirements

### Requirement: Gestión de cursos restringida al Administrador

El sistema SHALL restringir las operaciones de gestión de cursos (alta, listado administrativo, consulta, modificación, activación/desactivación y asignación de profesores) al rol Administrador. Un request sin sesión activa MUST responder HTTP 401; un request autenticado con un rol distinto de Administrador MUST responder HTTP 403 sin ejecutar la operación. La lectura `GET /api/courses/mine` queda exceptuada de esta restricción: es una lectura acotada al alcance de gestión de cada usuario y su comportamiento se define en la capability `enrollment-management`.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request de gestión a `/api/courses`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol no administrador
- **GIVEN** que un usuario con rol Estudiante o Profesor tiene sesión activa
- **WHEN** envía un request a los endpoints de gestión de cursos (alta, listado administrativo, consulta, modificación, activación/desactivación o profesores)
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

#### Scenario: Lectura acotada de cursos
- **GIVEN** que un usuario autenticado envía `GET /api/courses/mine`
- **WHEN** el sistema procesa el request
- **THEN** la operación se resuelve según la capability `enrollment-management` sin ser tratada como gestión administrativa