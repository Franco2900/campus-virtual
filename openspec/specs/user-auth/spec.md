# user-auth Specification

## Purpose
Permitir que un usuario no registrado cree una cuenta en el Campus Virtual usando un correo electrónico único, recibiendo inicialmente el rol Estudiante.

## Requirements

### Requirement: Registro de cuenta
El sistema SHALL permitir que un usuario no registrado cree una cuenta proporcionando nombre, apellido, correo electrónico y contraseña. Al completarse el registro, la cuenta MUST quedar almacenada y el sistema MUST confirmar el alta.

#### Scenario: Registro exitoso con datos válidos
- **WHEN** un usuario no registrado envía nombre, apellido, correo electrónico y contraseña válidos a `POST /api/auth/register`
- **THEN** el sistema crea la cuenta y responde con un estado de éxito (HTTP 201) junto con los datos de la cuenta creada, sin exponer la contraseña

#### Scenario: Correo electrónico no informado
- **WHEN** un usuario envía una solicitud de registro sin correo electrónico
- **THEN** el sistema rechaza la solicitud con un error de validación (HTTP 400) y no crea la cuenta

#### Scenario: Contraseña no informada
- **WHEN** un usuario envía una solicitud de registro sin contraseña
- **THEN** el sistema rechaza la solicitud con un error de validación (HTTP 400) y no crea la cuenta

### Requirement: Unicidad del correo electrónico
El correo electrónico SHALL ser el identificador único de la cuenta. El sistema MUST rechazar el registro cuando el correo ya esté asociado a otra cuenta.

#### Scenario: Correo ya registrado
- **WHEN** un usuario intenta registrarse con un correo electrónico que ya pertenece a otra cuenta
- **THEN** el sistema rechaza la solicitud (HTTP 409) con un mensaje que indica que el correo ya está registrado y no crea una nueva cuenta

#### Scenario: Correo ya registrado con distinta capitalización
- **WHEN** un usuario intenta registrarse con un correo que coincide con una cuenta existente salvo por mayúsculas/minúsculas
- **THEN** el sistema lo trata como correo ya registrado y rechaza la solicitud (HTTP 409)

### Requirement: Validación de los datos de registro
El sistema MUST validar el formato del correo electrónico y MUST rechazar los datos inválidos sin crear la cuenta. La contraseña MUST almacenarse de forma hasheada y nunca en texto plano.

#### Scenario: Correo electrónico con formato inválido
- **WHEN** un usuario envía un registro con un correo electrónico que no tiene formato válido
- **THEN** el sistema rechaza la solicitud (HTTP 400) y no crea la cuenta

#### Scenario: Contraseña que no cumple la longitud mínima
- **WHEN** un usuario envía un registro con una contraseña más corta que la longitud mínima definida
- **THEN** el sistema rechaza la solicitud (HTTP 400) y no crea la cuenta

#### Scenario: Contraseña almacenada de forma segura
- **WHEN** se crea una cuenta con una contraseña válida
- **THEN** la contraseña almacenada no es igual al texto plano ingresado y la contraseña no se devuelve en la respuesta

### Requirement: Rol inicial Estudiante
Toda cuenta creada mediante el registro SHALL recibir exactamente un rol, que inicialmente es Estudiante. El registro MUST NOT permitir que el usuario elija o reciba otro rol.

#### Scenario: Nueva cuenta recibe rol Estudiante
- **WHEN** un usuario completa un registro válido
- **THEN** la cuenta creada tiene el rol Estudiante y ningún otro rol

#### Scenario: Rol intentado en la solicitud es ignorado
- **WHEN** un usuario envía un registro válido incluyendo un campo de rol distinto de Estudiante
- **THEN** el sistema crea la cuenta con rol Estudiante, ignorando el rol solicitado

### Requirement: Autenticación de credenciales
El sistema SHALL permitir iniciar sesión a un usuario registrado validando su correo electrónico y contraseña. Cuando las credenciales son correctas, la sesión MUST quedar iniciada y el sistema MUST devolver los datos del usuario con su rol, sin exponer la contraseña. Cuando las credenciales son incorrectas, el sistema MUST responder con un único mensaje genérico de error (HTTP 401) sin revelar si lo incorrecto es el correo o la contraseña.

#### Scenario: Inicio de sesión exitoso
- **WHEN** un usuario registrado envía su correo electrónico y contraseña correctos a `POST /api/auth/login`
- **THEN** el sistema inicia una sesión y responde con un estado de éxito (HTTP 200) junto con los datos del usuario (incluido su rol), sin exponer la contraseña

#### Scenario: Credenciales incorrectas
- **WHEN** un usuario envía a `POST /api/auth/login` un correo electrónico o una contraseña que no coinciden con la cuenta registrada
- **THEN** el sistema responde con HTTP 401 y un mensaje genérico que no indica si falló el correo o la contraseña, y no inicia sesión

#### Scenario: Solicitud de inicio de sesión inválida
- **WHEN** un usuario envía a `POST /api/auth/login` una solicitud sin correo electrónico o sin contraseña
- **THEN** el sistema responde con un error de validación (HTTP 400) y no inicia sesión

### Requirement: Sesión activa persistente
Una vez iniciada la sesión, el sistema MUST mantenerla activa en el cliente mediante una cookie firmada, de forma que los requests posteriores del mismo usuario sean identificados hasta que la sesión se cierre o expire.

#### Scenario: La sesión persiste entre requests
- **WHEN** un usuario inicia sesión correctamente y luego realiza un request autenticado enviando la cookie de sesión
- **THEN** el sistema identifica al usuario como autenticado sin requerir que vuelva a ingresar sus credenciales

### Requirement: Consulta de sesión actual
El sistema SHALL permitir que un usuario con sesión activa consulte sus propios datos y rol a través de `GET /api/auth/me`. Este endpoint MUST requerir sesión activa: si no hay sesión, el sistema MUST responder HTTP 401.

#### Scenario: Usuario autenticado consulta su perfil
- **WHEN** un usuario con sesión activa envía `GET /api/auth/me`
- **THEN** el sistema responde HTTP 200 con los datos del usuario autenticado y su rol

#### Scenario: Usuario sin sesión consulta su perfil
- **WHEN** un usuario sin sesión activa envía `GET /api/auth/me`
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión

### Requirement: Cierre de sesión
El sistema SHALL permitir cerrar la sesión activa mediante `POST /api/auth/logout`. Tras el cierre el sistema MUST dejar de reconocer esa sesión; los requests autenticados posteriores con la misma cookie MUST responder HTTP 401. El cierre de sesión en estado ya no autenticado no MUST arrojar error.

#### Scenario: Usuario autenticado cierra sesión
- **WHEN** un usuario con sesión activa envía `POST /api/auth/logout`
- **THEN** el sistema finaliza la sesión y los requests autenticados posteriores de esa cookie responden HTTP 401

#### Scenario: Cierre de sesión sin sesión activa
- **WHEN** un usuario sin sesión activa envía `POST /api/auth/logout`
- **THEN** el sistema responde con éxito sin arrojar error, manteniendo el estado de no autenticado
