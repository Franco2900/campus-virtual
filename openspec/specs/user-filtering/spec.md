# user-filtering Specification

## Purpose
Permitir que el Administrador busque y filtre los usuarios registrados combinando texto libre, rol y estado sobre `GET /api/users`, manteniendo intacto el comportamiento del listado sin criterios y sin modificar los datos de las cuentas.

## Requirements

### Requirement: Filtrado de usuarios por criterios combinados

El sistema SHALL permitir al Administrador filtrar el listado de usuarios de `GET /api/users` mediante los query params opcionales `q` (texto libre), `role` (rol) y `active` (estado), combinados con semántica AND: un usuario se devuelve solo si satisface todos los criterios presentes. El criterio `q` MUST coincidir de forma parcial e insensible a mayúsculas contra el nombre, el apellido y el correo electrónico del usuario, y un valor de `q` vacío o en blanco MUST tratarse como ausente. Los criterios `role` y `active` MUST filtrar por igualdad exacta sobre el rol y el estado de la cuenta. La respuesta MUST conservar la misma forma que el listado sin filtros (arreglo de usuarios serializados con sus campos actuales) y el mismo orden por id. Cuando no se envía ningún criterio (o todos están vacíos), el sistema MUST devolver el listado completo, idéntico al comportamiento previo. El filtrado MUST incluir tanto cuentas activas como inactivas cuando el criterio `active` no está presente. Sin paginación: el sistema MUST devolver todos los usuarios que satisfacen los criterios.

#### Scenario: Listado sin criterios conserva el comportamiento actual
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** envía `GET /api/users` sin query params
- **THEN** el sistema responde HTTP 200 con todos los usuarios (activos e inactivos) ordenados por id, en la misma forma que antes del cambio

#### Scenario: Filtro por texto libre `q`
- **GIVEN** que existen usuarios con nombres, apellidos y correos diversos
- **WHEN** el Administrador envía `GET /api/users?q=ana`
- **THEN** el sistema responde HTTP 200 únicamente con los usuarios cuyo nombre, apellido o correo contienen «ana» de forma insensible a mayúsculas

#### Scenario: Filtro por rol `role`
- **GIVEN** que existen usuarios con roles Estudiante, Profesor y Administrador
- **WHEN** el Administrador envía `GET /api/users?role=student`
- **THEN** el sistema responde HTTP 200 únicamente con los usuarios cuyo rol es Estudiante

#### Scenario: Filtro por estado `active`
- **GIVEN** que existen usuarios activos y usuarios inactivos
- **WHEN** el Administrador envía `GET /api/users?active=false`
- **THEN** el sistema responde HTTP 200 únicamente con las cuentas inactivas

#### Scenario: Criterios combinados con AND
- **GIVEN** que existen usuarios con el mismo nombre parcial en distintos roles y estados
- **WHEN** el Administrador envía `GET /api/users?q=ana&role=student&active=true`
- **THEN** el sistema responde HTTP 200 solo con los usuarios que cumplen los tres criterios a la vez (nombre/apellido/correo contiene «ana», rol Estudiante y cuenta activa)

#### Scenario: `q` en blanco se trata como sin criterio
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** envía `GET /api/users?q=%20%20`
- **THEN** el sistema responde HTTP 200 con el listado completo, como si `q` no se hubiera enviado

### Requirement: Validación de los criterios de filtrado

El sistema MUST validar los criterios de filtrado en la capa de servicios y responder HTTP 400 con un mensaje claro en español cuando un criterio es inválido. El criterio `role` MUST aceptar únicamente los valores del enum de roles vigente (`student`, `teacher`, `admin`); cualquier otro valor MUST responder HTTP 400 sin ejecutar el listado. El criterio `active` MUST aceptar únicamente los strings `true` y `false`; cualquier otro valor, o un `active` sin valor, MUST responder HTTP 400 sin ejecutar el listado. Los criterios inválidos MUST rechazarse aunque los demás criterios sean válidos.

#### Scenario: `role` inválido
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** envía `GET /api/users?role=superuser`
- **THEN** el sistema responde HTTP 400 con un mensaje que indica que el rol es inválido, y no devuelve usuarios

#### Scenario: `active` inválido
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** envía `GET /api/users?active=maybe`
- **THEN** el sistema responde HTTP 400 con un mensaje claro, y no devuelve usuarios

#### Scenario: Un criterio inválido prevalece sobre uno válido
- **GIVEN** que un Administrador tiene sesión activa
- **WHEN** envía `GET /api/users?q=ana&role=invalido`
- **THEN** el sistema responde HTTP 400 sin devolver resultados parciales

### Requirement: Autorización del filtrado de usuarios

El filtrado de usuarios MUST quedar restringido al rol Administrador. Un request sin sesión activa MUST responder HTTP 401. Un request autenticado con un rol distinto de Administrador (Estudiante o Profesor) MUST responder HTTP 403 sin ejecutar el listado ni revelar datos de usuarios, con o sin criterios de filtrado.

#### Scenario: Acceso sin sesión
- **WHEN** un usuario sin sesión activa envía `GET /api/users?q=ana`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

#### Scenario: Rol no autorizado con criterios
- **GIVEN** que un usuario con rol Profesor tiene sesión activa
- **WHEN** envía `GET /api/users?role=student`
- **THEN** el sistema responde HTTP 403 y no devuelve usuarios

### Requirement: Estado vacío diferenciado del filtrado (flujo A1)

Cuando el filtrado no arroja coincidencias, el frontend MUST distinguir visualmente el estado «sin resultados para los criterios ingresados» del estado «todavía no hay usuarios registrados». El estado sin resultados MUST informar que no hay coincidencias para los criterios, MUST mostrar un ícono y MUST ofrecer una acción para limpiar los filtros. El estado «sin usuarios registrados» (listado global vacío, sin criterios) MUST conservar su mensaje actual.

#### Scenario: Sin coincidencias para los criterios (A1)
- **GIVEN** que el Administrador tiene criterios de filtrado activos que no coinciden con ningún usuario
- **WHEN** se muestra la pantalla de usuarios
- **THEN** la interfaz informa que no existen resultados para los criterios ingresados, con ícono y acción para limpiar los filtros, en lugar del mensaje de listado vacío

#### Scenario: Cero usuarios registrados sin criterios
- **GIVEN** que el sistema no tiene ningún usuario registrado y no hay criterios de filtrado
- **WHEN** el Administrador abre la pantalla de usuarios
- **THEN** la interfaz muestra el mensaje «Todavía no hay usuarios registrados.»

### Requirement: El filtrado es una operación de solo lectura

El filtrado de usuarios MUST limitarse a consultar y devolver usuarios; MUST NOT modificar, crear ni eliminar usuarios, inscripciones ni ningún otro dato, con independencia de los criterios ingresados. El filtrado MUST NOT generar notificaciones por correo electrónico.

#### Scenario: Consulta filtrada sin efectos sobre los datos
- **GIVEN** que un Administrador aplica filtros que devuelven uno o más usuarios
- **WHEN** la consulta finaliza con éxito
- **THEN** los usuarios devueltos conservan idénticos sus datos, rol y estado, y no se envía ningún correo electrónico
