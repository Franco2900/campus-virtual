# Spec Delta

## Purpose

Permitir al Administrador gestionar las cuentas de usuarios del Campus Virtual (consulta, edición de datos y rol, activación/desactivación lógica y reseteo de contraseña), garantizando que cada usuario posea exactamente un rol y protegiendo la continuidad del acceso administrativo.

## ADDED Requirements

### Requirement: Gestión de usuarios restringida al Administrador

El sistema SHALL restringir todas las operaciones de gestión de usuarios al rol Administrador. Un request sin sesión activa MUST responder HTTP 401; un request autenticado con un rol distinto de Administrador MUST responder HTTP 403 sin ejecutar la operación.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía cualquier request a `/api/users`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Acceso con rol no administrador
- **GIVEN** que un usuario con rol Estudiante o Profesor tiene sesión activa
- **WHEN** envía cualquier request a `/api/users`
- **THEN** el sistema responde HTTP 403 indicando falta de permisos y no ejecuta la operación

### Requirement: Consulta de usuarios

El sistema SHALL permitir al Administrador listar todas las cuentas y consultar una cuenta individual. El listado MUST incluir tanto cuentas activas como inactivas. Consultar un identificador inexistente MUST responder HTTP 404. La información devuelta MUST NOT incluir la contraseña ni su hash.

#### Scenario: Listado de usuarios
- **GIVEN** que existen cuentas activas e inactivas
- **WHEN** el Administrador envía `GET /api/users`
- **THEN** el sistema responde HTTP 200 con todas las cuentas, incluidas las inactivas, sin exponer la contraseña

#### Scenario: Consulta de usuario existente
- **GIVEN** que existe una cuenta con un identificador dado
- **WHEN** el Administrador envía `GET /api/users/<id>`
- **THEN** el sistema responde HTTP 200 con los datos de esa cuenta, sin exponer la contraseña

#### Scenario: Consulta de usuario inexistente
- **WHEN** el Administrador envía `GET /api/users/<id>` con un identificador que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Edición de datos y rol del usuario

El sistema SHALL permitir al Administrador modificar el nombre, apellido, correo electrónico y rol de una cuenta mediante `PUT /api/users/<id>`. El correo MUST ser válido y único de forma case-insensitive entre todas las cuentas; el rol MUST ser uno de los roles válidos (Estudiante, Profesor, Administrador). Modificar una cuenta inexistente MUST responder HTTP 404; datos inválidos MUST responder HTTP 400; un correo que colisione con otra cuenta MUST responder HTTP 409; en caso de éxito MUST responder HTTP 200 con la cuenta actualizada.

#### Scenario: Edición exitosa de datos y rol
- **GIVEN** que existe una cuenta y que los nuevos datos son válidos y no colisionan con otro correo
- **WHEN** el Administrador envía `PUT /api/users/<id>`
- **THEN** el sistema responde HTTP 200 con la cuenta actualizada

#### Scenario: Cambio de rol de Estudiante a Profesor
- **GIVEN** que existe una cuenta con rol Estudiante
- **WHEN** el Administrador cambia su rol a Profesor
- **THEN** el sistema responde con éxito y la cuenta queda con el rol Profesor y ningún otro rol

#### Scenario: Correo ya utilizado por otra cuenta
- **GIVEN** que otra cuenta ya usa un correo dado
- **WHEN** el Administrador intenta asignar ese correo a una cuenta distinta
- **THEN** el sistema responde HTTP 409 y no modifica la cuenta

#### Scenario: Rol inválido
- **WHEN** el Administrador envía `PUT /api/users/<id>` con un rol que no es válido
- **THEN** el sistema responde HTTP 400 y no modifica la cuenta

### Requirement: Activación y desactivación lógica de usuarios

El sistema SHALL permitir al Administrador cambiar el estado de una cuenta entre activa e inactiva mediante `PATCH /api/users/<id>` con body `{"active": <bool>}`, sin borrado físico. Operar sobre una cuenta inexistente MUST responder HTTP 404; un body sin booleano `active` MUST responder HTTP 400; en caso de éxito la respuesta MUST reflejar el nuevo estado.

#### Scenario: Desactivación de usuario
- **GIVEN** que existe una cuenta activa
- **WHEN** el Administrador envía `PATCH /api/users/<id>` indicando desactivar
- **THEN** el sistema responde con éxito y la cuenta queda inactiva, sin eliminarse

#### Scenario: Reactivación de usuario
- **GIVEN** que existe una cuenta inactiva
- **WHEN** el Administrador envía `PATCH /api/users/<id>` indicando activar
- **THEN** el sistema responde con éxito y la cuenta queda activa

#### Scenario: Operación sobre usuario inexistente
- **WHEN** el Administrador envía `PATCH /api/users/<id>` con un identificador que no existe
- **THEN** el sistema responde HTTP 404

### Requirement: Reseteo de contraseña por el Administrador

El sistema SHALL permitir al Administrador fijar una nueva contraseña a una cuenta mediante `POST /api/users/<id>/password` con body `{"password": <str>}`. La contraseña MUST cumplir la longitud mínima vigente; una contraseña inválida MUST responder HTTP 400; una cuenta inexistente MUST responder HTTP 404. La contraseña MUST almacenarse hasheada y MUST NOT devolverse en la respuesta ni registrarse en logs.

#### Scenario: Reseteo exitoso
- **GIVEN** que existe una cuenta y que la nueva contraseña cumple los requisitos
- **WHEN** el Administrador envía `POST /api/users/<id>/password`
- **THEN** el sistema responde con éxito y el usuario puede autenticarse con la nueva contraseña

#### Scenario: Contraseña inválida
- **WHEN** el Administrador envía una contraseña que no cumple la longitud mínima
- **THEN** el sistema responde HTTP 400 y no modifica la contraseña

### Requirement: Protección de la autogestión del Administrador

El sistema MUST NOT permitir que un Administrador desactive su propia cuenta ni que se asigne a sí mismo un rol distinto de Administrador. Cualquiera de esas operaciones MUST responder HTTP 400 con un mensaje claro y MUST NOT modificar la cuenta.

#### Scenario: Autodesactivación bloqueada
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** intenta desactivar su propia cuenta
- **THEN** el sistema responde HTTP 400 y la cuenta permanece activa

#### Scenario: Autocambio de rol bloqueado
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** intenta cambiar su propio rol a Estudiante o Profesor
- **THEN** el sistema responde HTTP 400 y la cuenta conserva el rol Administrador
