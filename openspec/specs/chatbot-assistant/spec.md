# chatbot-assistant Specification

## Purpose

Permitir que un usuario autenticado (Estudiante, Profesor o Administrador) utilice un chatbot de asistencia basado en LangChain + Ollama local (modelo `qwen3:4b`, configurable) para consultar sobre el funcionamiento de la plataforma y obtener información real del sistema, respetando los permisos de su rol, sin realizar operaciones de escritura, sin calificar ni corregir entregas, manteniendo un historial de conversaciones aislado por usuario y respondiendo de manera clara y amable en español.

## Requirements

### Requirement: Acceso al chatbot solo para usuarios autenticados

El sistema SHALL permitir el acceso a la funcionalidad del chatbot únicamente a usuarios autenticados con rol Estudiante, Profesor o Administrador. Un usuario sin sesión activa MUST recibir una respuesta HTTP 401 cuando intente utilizar el endpoint del chatbot. La interfaz de usuario de `/chat` MUST impedir el acceso o redirigir al inicio de sesión cuando no exista una sesión válida. Esta restricción aplica tanto al acceso inicial como a la ejecución de consultas.

#### Scenario: Usuario no autenticado intenta acceder al chatbot (A1)
- **GIVEN** que un usuario no ha iniciado sesión
- **WHEN** intenta acceder a `/chat` o enviar una consulta al chatbot
- **THEN** el sistema responde HTTP 401 indicando que se requiere iniciar sesión para utilizar el chatbot
- **AND** la interfaz orienta al usuario a iniciar sesión

#### Scenario: Usuario autenticado con rol válido accede al chatbot
- **GIVEN** que un usuario autenticado con rol Estudiante, Profesor o Administrador tiene sesión activa
- **WHEN** accede a la interfaz del chatbot
- **THEN** el sistema habilita la interfaz de conversación
- **AND** permite enviar consultas

#### Scenario: Usuario autenticado pero rol no contemplado es rechazado
- **GIVEN** que un usuario autenticado con un rol no contemplado en CU-11 intenta utilizar el chatbot
- **WHEN** envía una consulta
- **THEN** el sistema aplica las validaciones de autorización correspondientes y responde conforme a su rol (o 403 según corresponda)

### Requirement: Conversación, idioma, extensión y contexto

El chatbot SHALL responder en español, con tono claro y amable, adaptando la extensión de sus respuestas a cada consulta (regla 12). Para generar la respuesta, el chatbot SHALL analizar la consulta para determinar la información necesaria (paso 5 del flujo principal). Si la consulta requiere contexto de la conversación en curso, el chatbot SHALL utilizar el contexto de la conversación actual (paso 8). Si la consulta hace referencia a una conversación anterior (A8), el chatbot SHALL recuperar y utilizar el historial disponible correspondiente únicamente al mismo usuario autenticado (reglas 13 y 15). Cuando no disponga del contexto necesario para interpretar la consulta, el chatbot SHALL informar esa limitación y solicitar la información que falte cuando sea necesario (A8 paso 4).

#### Scenario: Respuesta en español con extensión adaptada
- **GIVEN** que un usuario autenticado envía una consulta sencilla o detallada al chatbot
- **WHEN** el chatbot genera la respuesta
- **THEN** la respuesta está escrita en español, con tono claro y amable
- **AND** su extensión se adapta a la complejidad de la consulta

#### Scenario: Consulta hace referencia a conversación anterior (A8)
- **GIVEN** que un usuario autenticado tiene un historial previo de conversaciones
- **WHEN** envía una consulta que hace referencia a una conversación anterior
- **THEN** el chatbot recupera el historial disponible correspondiente únicamente a ese usuario
- **AND** utiliza dicho contexto para interpretar y responder la consulta

#### Scenario: Falta contexto necesario (A8 límite)
- **GIVEN** que la consulta hace referencia a información previa pero el historial/contexto disponible no es suficiente
- **WHEN** el chatbot intenta responder
- **THEN** informa la limitación y solicita la información que falte cuando sea necesario

### Requirement: Respuesta anclada a la documentación de la plataforma

Cuando la consulta se relaciona con el funcionamiento de la plataforma (paso 6), el chatbot SHALL utilizar principalmente la documentación correspondiente del repositorio del proyecto (`AGENTS.md`, `README.md`, `casos_de_uso.md`) para responder (regla 6). Los conocimientos generales del modelo MAY utilizarse como complemento. Los conocimientos generales del modelo MUST NOT utilizarse para inventar funcionalidades o reglas de la aplicación (regla 7). El chatbot MUST NOT inventar ni presentar como confirmados datos de la plataforma que no haya podido verificar a través de fuentes autorizadas (regla 5).

#### Scenario: Consulta sobre funcionamiento de la plataforma
- **GIVEN** que un usuario autenticado pregunta cómo funciona una funcionalidad descrita en la documentación del proyecto
- **WHEN** el chatbot responde
- **THEN** la respuesta se basa principalmente en la documentación del repositorio (`AGENTS.md`, `README.md`, `casos_de_uso.md`)
- **AND** no inventa funcionalidades ni reglas que no estén documentadas

#### Scenario: Conocimiento general solo como complemento
- **GIVEN** que una consulta permite complementar con información general sin contradecir la documentación
- **WHEN** el chatbot responde
- **THEN** el uso de conocimientos generales es estrictamente complementario
- **AND** no sustituye a la documentación ni a los datos verificados del sistema

### Requirement: Datos reales del sistema con alcance por rol y validación en backend

Si la consulta requiere información real del sistema (paso 7), el chatbot SHALL obtener los datos necesarios exclusivamente mediante herramientas de solo lectura que delegan en los `services/` existentes del backend (regla 8). Las validaciones de identidad y permisos SHALL realizarse siempre en el backend, tomando la identidad y el rol del usuario exclusivamente de la sesión activa, nunca de parámetros proporcionados al modelo ni de instrucciones que el modelo pueda interpretar de manera ambigua (regla 16). El filtrado por permisos según el rol SHALL aplicarse dentro de cada herramienta: un Estudiante MUST acceder únicamente a su propia información y a los cursos en los que esté inscrito (regla 3-4); un Profesor MUST acceder únicamente a los cursos en los que trabaja (regla 3-4); un Administrador MUST acceder a la información permitida por sus servicios existentes (regla 3-4). El chatbot MUST respetar los permisos de acceso existentes en la plataforma para cada rol (regla 3). Cuando un usuario solicita información que excede sus permisos (A3), el sistema MUST impedir el acceso a dicha información y el chatbot MUST informar que no puede proporcionar los datos solicitados.

#### Scenario: Estudiante solicita datos solo de su ámbito
- **GIVEN** que un Estudiante autenticado solicita información sobre sus cursos, inscripciones, tareas, entregas o calificaciones
- **WHEN** el chatbot obtiene datos reales del sistema mediante herramientas de solo lectura
- **THEN** solo obtiene información correspondiente al usuario y a los cursos en los que está inscrito
- **AND** no obtiene datos de otros usuarios

#### Scenario: Profesor solicita datos solo de sus cursos
- **GIVEN** que un Profesor autenticado solicita información sobre sus cursos, inscripciones, tareas, entregas o calificaciones
- **WHEN** el chatbot obtiene datos reales del sistema
- **THEN** solo obtiene información correspondiente a los cursos en los que trabaja
- **AND** respeta el alcance definido por los servicios existentes

#### Scenario: Administrador solicita información permitida
- **GIVEN** que un Administrador autenticado solicita información del sistema
- **WHEN** el chatbot obtiene datos reales del sistema
- **THEN** los datos se obtienen respetando los permisos definidos en los servicios del backend
- **AND** sin exceder el alcance autorizado

#### Scenario: Solicitud de información no autorizada (A3)
- **GIVEN** que un usuario solicita información que excede los permisos de su rol
- **WHEN** el chatbot procesa la solicitud
- **THEN** el sistema impide el acceso a dicha información
- **AND** el chatbot informa que no puede proporcionar los datos solicitados

#### Scenario: Identidad y permisos siempre desde sesión en backend
- **GIVEN** que se intenta proporcionar rol/identidad al modelo o a la herramienta desde el lado cliente
- **WHEN** la herramienta consulta datos
- **THEN** la herramienta valida la sesión activa en el backend
- **AND** obtiene identidad y rol exclusivamente desde la sesión, sin confiar en parámetros externos

### Requirement: Rechazo de mutaciones, corrección y calificación

El chatbot MUST ser exclusivamente de solo lectura (regla 8). El chatbot MUST NOT crear, modificar ni eliminar información de la plataforma, ni ejecutar operaciones en nombre del usuario (regla 8). Cuando el usuario solicita crear, modificar o eliminar información (A4), el chatbot MUST informar que no puede ejecutar esa operación y, cuando corresponda, orientar al usuario hacia la funcionalidad correspondiente de la plataforma. El chatbot MUST NOT corregir entregas ni asignar calificaciones (regla 9). Cuando el usuario solicita corregir una entrega o asignar una calificación (A5), el chatbot MUST informar que esas operaciones no forman parte de sus funciones y que corresponden al profesor. Ninguna herramienta expuesta al agente MAY realizar operaciones de escritura, modificación, eliminación, corrección o calificación.

#### Scenario: Solicitud de modificación o ejecución de operaciones (A4)
- **GIVEN** que un usuario solicita crear, modificar o eliminar información de la plataforma mediante el chatbot
- **WHEN** el chatbot responde
- **THEN** informa que no puede ejecutar esa operación
- **AND** orienta al usuario hacia la funcionalidad correspondiente cuando corresponda

#### Scenario: Solicitud de corrección o calificación de tareas (A5)
- **GIVEN** que un usuario solicita que el chatbot corrija una entrega o asigne una calificación
- **WHEN** el chatbot responde
- **THEN** informa que esas operaciones no forman parte de sus funciones
- **AND** aclara que corresponden al profesor

#### Scenario: Garantía de solo lectura
- **GIVEN** que se intenta cualquier operación de escritura a través de las herramientas del chatbot
- **WHEN** se procesa la solicitud
- **THEN** el backend rechaza la operación
- **AND** no se modifica, crea ni elimina ningún dato en el sistema

### Requirement: Consulta sin información suficiente

Cuando el chatbot no dispone de información suficiente para responder con certeza (A2), este MUST reconocer sus limitaciones, evitar especular y, cuando resulte útil, proporcionar información general relacionada sin presentarla como dato confirmado de la plataforma (A2 pasos 2-3). Cuando corresponda, el chatbot SHALL recomendar consultar con un profesor o administrador (regla 10, A2 paso 4).

#### Scenario: Consulta sobre información no disponible (A2)
- **GIVEN** que el usuario realiza una consulta que requiere información no disponible o que no puede determinarse con suficiente certeza
- **WHEN** el chatbot responde
- **THEN** informa que no dispone de información suficiente para responder con certeza
- **AND** no presenta información no verificada como confirmada

#### Scenario: Información general relacionada sin especulación
- **GIVEN** que resulta útil ofrecer contexto general ante falta de datos concretos
- **WHEN** el chatbot responde
- **THEN** aclara que es información general relacionada
- **AND** evita especular sobre datos específicos del sistema

#### Scenario: Recomendación a profesor o administrador
- **GIVEN** que, ante falta de información suficiente, corresponde derivar a soporte humano según el caso
- **WHEN** el chatbot responde
- **THEN** recomienda consultar con un profesor o administrador cuando corresponda

### Requirement: Consulta ajena a la plataforma

Cuando el usuario realiza una consulta ajena a la función del chatbot (A6), el chatbot SHALL explicar brevemente que su función es ayudar a utilizar la plataforma y consultar información del sistema (regla 11, A6 paso 2). El chatbot SHALL redirigir al usuario hacia ese propósito sin responder la consulta ajena a su función (A6 paso 3).

#### Scenario: Consulta ajena a la función del chatbot (A6)
- **GIVEN** que un usuario realiza una consulta que no está relacionada con el funcionamiento de la plataforma educativa
- **WHEN** el chatbot responde
- **THEN** explica brevemente que su función es ayudar a utilizar la plataforma y consultar información del sistema
- **AND** redirige al usuario hacia ese propósito
- **AND** no responde la consulta ajena

### Requirement: Error del servicio

Cuando se produce un error que impide consultar la base de datos o generar una respuesta (A7), el chatbot SHALL informar que no pudo completar la consulta (A7 paso 2). Cuando corresponda, el chatbot SHALL indicar que el usuario puede intentarlo nuevamente (A7 paso 3). Esta respuesta debe ser clara y amable, independientemente de que el error sea debido a Ollama caído, modelo no disponible, fallo de conexión u otro error del servicio (la ejecución local con Ollama figura como restricción del stack tecnológico del proyecto, no como regla de CU-11). El backend SHALL traducir errores técnicos del servicio LLM a una respuesta adecuada para el usuario.

#### Scenario: Error al consultar información o generar respuesta (A7)
- **GIVEN** que ocurre un error al consultar la base de datos o al generar una respuesta (incluyendo Ollama no disponible o modelo `qwen3:4b` no descargado)
- **WHEN** el chatbot responde
- **THEN** informa que no pudo completar la consulta
- **AND** sugiere reintentar cuando corresponda
- **AND** el mensaje es claro y amable, sin exponer detalles técnicos sensibles innecesarios

#### Scenario: Servicio LLM local no disponible
- **GIVEN** que el servicio Ollama local no está ejecutándose o el modelo `qwen3:4b` no está disponible
- **WHEN** el usuario envía una consulta
- **THEN** el backend detecta el error y el chatbot informa que no pudo completar la consulta
- **AND** sugiere intentarlo nuevamente

### Requirement: Historial persistido por usuario y aislamiento

El sistema SHALL persistir el historial de conversaciones en SQLite mediante tablas nuevas creadas por migración incremental de Flask-Migrate/Alembic (patrón de `backend/migrations/`, posterior a `0007` según propuesta). El historial de conversaciones SHALL mantenerse asociado al usuario correspondiente (regla 13). El historial de conversaciones MUST NO ser accesible por otros usuarios sin autorización (regla 13). Cada usuario accede únicamente a su propio historial; el aislamiento entre usuarios es obligatorio. El historial se utiliza como contexto en conversaciones futuras (paso 8, A8) y, al utilizarlo, el chatbot SHALL priorizar los datos actuales y verificados del sistema cuando la consulta requiera información actualizada. La persistencia del historial no modifica datos del sistema (postcondición).

#### Scenario: Historial asociado al usuario correspondiente
- **GIVEN** que un usuario autenticado mantiene una conversación con el chatbot
- **WHEN** los mensajes se almacenan
- **THEN** quedan asociados únicamente a ese `user_id`
- **AND** se preserva la secuencia de la conversación

#### Scenario: Aislamiento entre usuarios
- **GIVEN** que existen conversaciones de distintos usuarios
- **WHEN** un usuario solicita recuperar historial o se utiliza contexto
- **THEN** únicamente se recupera el historial correspondiente a ese usuario
- **AND** nunca se accede al historial de otros usuarios

#### Scenario: Priorizar datos actuales sobre historial al responder
- **GIVEN** que el historial contiene información previa y la consulta requiere información actualizada del sistema
- **WHEN** el chatbot genera la respuesta
- **THEN** prioriza los datos actuales y verificados obtenidos desde los servicios autorizados del sistema
- **AND** no presenta datos desactualizados del historial como definitivos si hay información actual verificable

#### Scenario: Persistencia sin modificación de datos
- **GIVEN** que se almacena el historial de una conversación
- **WHEN** la operación de guardado concluye
- **THEN** no se crea, modifica ni elimina ninguna entidad del dominio (cursos, usuarios, inscripciones, tareas, entregas, calificaciones)
- **AND** únicamente se actualizan las tablas de historial

### Requirement: Eliminación del historial propio

El sistema SHALL permitir a un usuario autenticado (Estudiante, Profesor o Administrador) eliminar completamente su propio historial de conversaciones con el chatbot mediante `DELETE /api/chat/messages` (A9). Un usuario sin sesión MUST recibir HTTP 401. La operación SHALL ser idempotente: cuando el usuario no tiene historial (o ya lo eliminó), el sistema MUST responder con éxito en lugar de un error. El borrado SHALL alcanzar únicamente al usuario autenticado y MUST NO eliminar datos funcionales de la plataforma como cursos, tareas, entregas, inscripciones ni calificaciones (regla 14). La identidad y el permiso de borrado SHALL validarse en el backend desde la sesión activa, sin depender de instrucciones proporcionadas al modelo (regla 16). El historial eliminado MUST dejar de utilizarse como contexto en futuras consultas y no MUST volver a incorporarse desde copias de trabajo, cachés ni memorias persistentes controladas por la aplicación (regla 17). La eliminación la gestiona el sistema (endpoint y opción de la interfaz), no una herramienta del agente: el chatbot MUST seguir siendo de solo lectura y ninguna herramienta expuesta al agente MAY ejecutar esta operación (regla 8, que autoriza expresamente solo esta excepción vía sistema). La interfaz de `/chat` SHALL ofrecer la opción de eliminar el historial con confirmación previa que informe que la operación no podrá recuperarse desde la aplicación (A9 pasos 3-5); al cancelar, el sistema MUST conservar el historial existente (A9.1). Cuando el usuario solicita el borrado como consulta al chatbot, el asistente MUST orientarlo hacia la opción de la interfaz sin prometer ejecutar el borrado.

#### Scenario: Confirmar la eliminación borra todo el historial
- **GIVEN** que un usuario autenticado tiene un historial de conversaciones con el chatbot
- **WHEN** selecciona la opción de eliminar historial, confirma la operación en el diálogo de confirmación y el sistema la procesa
- **THEN** todas sus conversaciones y mensajes almacenados quedan eliminados
- **AND** el contexto del chatbot queda vacío para sus futuras consultas (A9 paso 9)
- **AND** el sistema muestra la confirmación de que la eliminación se completó (A9 paso 8)

#### Scenario: Cancelar la eliminación no borra nada (A9.1)
- **GIVEN** que un usuario autenticado abrió el diálogo de confirmación de eliminación de historial
- **WHEN** cancela la operación antes de confirmarla
- **THEN** el historial existente se conserva íntegro
- **AND** el usuario puede continuar utilizando el chatbot con su contexto previo

#### Scenario: Sin sesión la eliminación es rechazada
- **GIVEN** que una persona no ha iniciado sesión
- **WHEN** intenta eliminar el historial con `DELETE /api/chat/messages`
- **THEN** el sistema responde HTTP 401
- **AND** no se elimina ningún dato

#### Scenario: Eliminación idempotente sin historial
- **GIVEN** que un usuario autenticado no tiene historial de conversaciones (o ya lo eliminó previamente)
- **WHEN** ejecuta la eliminación
- **THEN** el sistema responde HTTP 200 con éxito, sin error
- **AND** la interfaz continúa en el estado vacío sin mensajes de error

#### Scenario: El borrado alcanza solo al usuario propio y no toca datos funcionales
- **GIVEN** que un usuario autenticado elimina su historial
- **WHEN** la operación concluye
- **THEN** solo se eliminan las conversaciones y mensajes de chat de ese usuario
- **AND** el historial de otros usuarios queda intacto
- **AND** no se ven afectados cursos, tareas, entregas, inscripciones ni calificaciones (regla 14)

### Requirement: Ejecución local con Ollama y configuración

El chatbot SHALL ejecutarse localmente: el modelo de lenguaje y el procesamiento de las consultas ocurren en el entorno del sistema, sin depender de servicios externos en la nube (restricción del stack tecnológico del proyecto; no es una regla de CU-11). El agente LangChain SHALL utilizar Ollama local con el modelo `qwen3:4b` (configurable por nombre de modelo y URL de Ollama a través de variables de entorno, con valores por defecto para desarrollo). La implementación SHALL utilizar `langchain-ollama` según las decisiones del proyecto. El sistema SHALL documentar el requisito de tener Ollama ejecutándose localmente y el modelo `qwen3:4b` descargado (p.ej. `ollama pull qwen3:4b`).

#### Scenario: Ejecución exclusivamente local
- **GIVEN** que el chatbot procesa una consulta
- **WHEN** el agente de IA genera la respuesta
- **THEN** utiliza Ollama local con el modelo configurado
- **AND** no realiza llamadas a servicios externos en la nube

#### Scenario: Modelo y URL configurables
- **GIVEN** que se configuran variables de entorno para el nombre del modelo y la URL de Ollama
- **WHEN** el servicio del chatbot se inicializa
- **THEN** utiliza dichos valores para conectar con Ollama local
- **AND** permite cambiar el modelo sin modificar el código

#### Scenario: Dependencias documentadas para ejecución local
- **GIVEN** que un entorno de desarrollo/despliegue local desea utilizar el chatbot
- **WHEN** se sigue la documentación
- **THEN** se indica que Ollama debe estar ejecutándose y que el modelo `qwen3:4b` debe estar descargado

### Requirement: Flujo principal completo y postcondiciones

El flujo principal (pasos 1-11) SHALL cumplirse cuando un usuario autenticado accede al chatbot, envía una consulta y recibe una respuesta. Las postcondiciones establecidas en CU-11 SHALL satisfacerse: el usuario recibe una respuesta o una explicación de por qué no puede responderse su consulta; la información proporcionada respeta los permisos de acceso correspondientes al rol del usuario; las consultas de información se realizan sin modificar los datos de la plataforma; y el historial de conversaciones se conserva asociado a la cuenta del usuario para permitir su utilización como contexto en futuras conversaciones.

#### Scenario: Flujo principal completo
- **GIVEN** que un usuario autenticado con rol válido accede al chatbot
- **WHEN** envía una consulta válida relacionada con la plataforma o que requiere datos autorizados
- **THEN** el sistema ejecuta los pasos 1-11 del flujo principal
- **AND** muestra una respuesta en español, clara y amable, adaptada a la consulta
- **AND** la información respeta los permisos del rol

#### Scenario: Postcondición - respuesta o explicación
- **GIVEN** que el usuario envía cualquier consulta al chatbot
- **WHEN** el proceso concluye
- **THEN** el usuario recibe una respuesta o una explicación clara de por qué no puede responderse su consulta
- **AND** nunca queda la solicitud sin respuesta o explicación

#### Scenario: Postcondición - sin modificación de datos
- **GIVEN** que se procesa una consulta de información
- **WHEN** concluye exitosamente
- **THEN** no se modifica ningún dato de la plataforma
- **AND** las operaciones realizadas son exclusivamente de lectura o de persistencia del propio historial

#### Scenario: Postcondición - historial conservado para contexto futuro
- **GIVEN** que la conversación ocurre entre un usuario autenticado y el chatbot
- **WHEN** los mensajes se procesan
- **THEN** el historial queda asociado a la cuenta del usuario
- **AND** puede reutilizarse como contexto en futuras conversaciones del mismo usuario

### Requirement: Integración con arquitectura existente y endpoints

La implementación del chatbot SHALL seguir las capas establecidas: `routes → services → models` (regla backend). SHALL crear un blueprint nuevo `backend/blueprints/chat.py` registrado en `app.py`, un servicio nuevo `backend/services/chat_service.py` (orquestación del agente y herramientas de solo lectura delegando en los `services/` existentes), modelos nuevos de historial en `backend/models/` y migración incremental en `backend/migrations/` (post `0007`). No SHALL modificar contratos, endpoints ni comportamiento de CU-01 a CU-10 existentes. El frontend SHALL implementar la feature en `frontend/src/features/chatbot/` con página `/chat` enlazada desde el sidebar para los tres roles, utilizando el design system (`src/ui/`, tokens, sin colores hardcodeados), y consumiendo el backend a través de `src/api/client.js`. Las dependencias `langchain` y `langchain-ollama` SHALL añadirse a `backend/requirements.txt` con versiones fijadas.

#### Scenario: Estructura backend conforme a arquitectura
- **GIVEN** que se implementa el chatbot
- **WHEN** se revisa la organización del código
- **THEN** el blueprint está en `backend/blueprints/chat.py`, el servicio en `backend/services/chat_service.py`, los modelos de historial en `backend/models/`
- **AND** la lógica de negocio reside en `services/`, no en `routes/` ni en modelos
- **AND** las herramientas delegan en los `services/` existentes sin SQL crudo

#### Scenario: Integración frontend con design system
- **GIVEN** que se implementa la página `/chat`
- **WHEN** se construye la interfaz
- **THEN** utiliza componentes reutilizables de `src/ui/`, tokens de `src/theme/` y ThemeProvider
- **AND** no usa colores hardcodeados
- **AND** se comunica con el backend vía `src/api/client.js`

#### Scenario: Migración incremental y no invasiva
- **GIVEN** que se añade el historial
- **WHEN** se genera la migración
- **THEN** es incremental (Flask-Migrate/Alembic), posterior a `0007`
- **AND** aplica correctamente con `flask db upgrade` en Windows, Linux y macOS
- **AND** no altera entidades existentes
