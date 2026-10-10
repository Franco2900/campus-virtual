# course-management Specification

## Purpose
Permitir al Administrador dar de alta, consultar, modificar, desactivar y reactivar cursos del Campus Virtual, y proveer la cuenta de Administrador inicial necesaria para operar esta gestión.

## Requirements

### Requirement: Provisión del Administrador inicial

El sistema SHALL proveer un mecanismo de arranque que cree una cuenta con rol Administrador a partir de credenciales provistas por variables de entorno obligatorias, para poder operar las funciones administrativas de forma reproducible. El correo y la contraseña MUST tomarse de variables de entorno (`CAMPUS_ADMIN_EMAIL`, `CAMPUS_ADMIN_PASSWORD`); si alguna falta, la operación MUST fallar con un mensaje claro y MUST NOT crear ni modificar cuentas. La operación MUST ser idempotente: si ya existe una cuenta con ese correo, MUST NOT duplicarla ni fallar.

#### Scenario: Provisión exitosa del administrador
- **GIVEN** que no existe una cuenta con el correo administrador y que las variables de entorno obligatorias están definidas
- **WHEN** se ejecuta el mecanismo de provisión
- **THEN** el sistema crea una cuenta con rol Administrador que puede iniciar sesión, sin exponer la contraseña

#### Scenario: Variables de entorno faltantes
- **GIVEN** que falta `CAMPUS_ADMIN_EMAIL` o `CAMPUS_ADMIN_PASSWORD`
- **WHEN** se ejecuta el mecanismo de provisión
- **THEN** el sistema falla con un mensaje claro y no crea ninguna cuenta

#### Scenario: Provisionamiento repetido
- **GIVEN** que ya existe una cuenta con el correo administrador
- **WHEN** se ejecuta el mecanismo de provisión otra vez
- **THEN** el sistema no duplica ni modifica la cuenta existente y no arroja error

### Requirement: Gestión de cursos restringida al Administrador

El sistema SHALL restringir todas las operaciones de gestión de cursos al rol Administrador. Un request sin sesión activa MUST responder HTTP 401; un request autenticado con un rol distinto de Administrador MUST responder HTTP 403 sin ejecutar la operación.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request a `/api/courses`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol no administrador
- **GIVEN** que un usuario con rol Estudiante o Profesor tiene sesión activa
- **WHEN** envía cualquier request a `/api/courses`
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

### Requirement: Creación de cursos

El sistema SHALL permitir al Administrador crear un curso mediante `POST /api/courses` indicando nombre, código y descripción. El nombre y el código MUST ser obligatorios y no vacíos; el código MUST ser único de forma case-insensitive; el nombre MAY repetirse. Un curso creado MUST quedar activo. Ante datos inválidos el sistema MUST responder HTTP 400; ante un código ya existente MUST responder HTTP 409; en caso de éxito MUST responder HTTP 201 con el curso creado.

#### Scenario: Alta exitosa de curso
- **GIVEN** un curso enviado con nombre, código y descripción válidos que no repite un código existente
- **WHEN** el Administrador envía `POST /api/courses`
- **THEN** el sistema responde HTTP 201 con el curso creado en estado activo

#### Scenario: Datos obligatorios faltantes
- **WHEN** el Administrador envía `POST /api/courses` sin nombre o sin código
- **THEN** el sistema responde HTTP 400 y no crea el curso

#### Scenario: Código duplicado
- **GIVEN** que existe un curso con un código dado
- **WHEN** el Administrador intenta crear otro curso con el mismo código (aunque difiera en mayúsculas y minúsculas)
- **THEN** el sistema responde HTTP 409 y no crea el curso

### Requirement: Consulta de cursos

El sistema SHALL permitir al Administrador listar todos los cursos y consultar un curso individual. El listado MUST incluir tanto cursos activos como inactivos. Consultar un identificador inexistente MUST responder HTTP 404.

#### Scenario: Listado de cursos
- **GIVEN** que existen cursos activos e inactivos
- **WHEN** el Administrador envía `GET /api/courses`
- **THEN** el sistema responde HTTP 200 con todos los cursos, incluidos los inactivos

#### Scenario: Consulta de curso existente
- **GIVEN** que existe un curso con un identificador dado
- **WHEN** el Administrador envía `GET /api/courses/<id>`
- **THEN** el sistema responde HTTP 200 con la información de ese curso

#### Scenario: Consulta de curso inexistente
- **WHEN** el Administrador envía `GET /api/courses/<id>` con un identificador que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Modificación de cursos

El sistema SHALL permitir al Administrador modificar los datos de un curso existente mediante `PUT /api/courses/<id>`. Las mismas validaciones de creación MUST aplicarse (nombre y código obligatorios, código único case-insensitive). Modificar un curso inexistente MUST responder HTTP 404; un código que colisione con otro curso MUST responder HTTP 409; en caso de éxito MUST responder HTTP 200 con el curso actualizado.

#### Scenario: Modificación exitosa
- **GIVEN** que existe un curso y que los nuevos datos son válidos y no colisionan con otro código
- **WHEN** el Administrador envía `PUT /api/courses/<id>`
- **THEN** el sistema responde HTTP 200 con el curso actualizado

#### Scenario: Modificación de curso inexistente
- **WHEN** el Administrador envía `PUT /api/courses/<id>` con un identificador que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Desactivación y reactivación de cursos

El sistema SHALL permitir al Administrador cambiar el estado de un curso entre activo e inactivo mediante `PATCH /api/courses/<id>`, sin borrado físico. Desactivar un curso MUST dejarlo inactivo; reactivarlo MUST dejarlo activo. Un curso inactivo MUST NOT tratarse como activo. Operar sobre un curso inexistente MUST responder HTTP 404; en caso de éxito la respuesta MUST reflejar el nuevo estado.

#### Scenario: Desactivación de curso
- **GIVEN** que existe un curso activo
- **WHEN** el Administrador envía `PATCH /api/courses/<id>` indicando desactivar
- **THEN** el sistema responde con éxito y el curso queda en estado inactivo, sin eliminarse

#### Scenario: Reactivación de curso
- **GIVEN** que existe un curso inactivo
- **WHEN** el Administrador envía `PATCH /api/courses/<id>` indicando activar
- **THEN** el sistema responde con éxito y el curso queda en estado activo

#### Scenario: Operación sobre curso inexistente
- **WHEN** el Administrador envía `PATCH /api/courses/<id>` con un identificador que no existe
- **THEN** el sistema responde HTTP 404
