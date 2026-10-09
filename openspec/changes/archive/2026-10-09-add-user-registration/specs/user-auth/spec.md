# Spec Delta

## Purpose

Permitir que un usuario no registrado cree una cuenta en el Campus Virtual usando un correo electrónico único, recibiendo inicialmente el rol Estudiante.

## ADDED Requirements

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
