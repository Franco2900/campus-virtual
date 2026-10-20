# Spec Delta

## ADDED Requirements

### Requirement: Priorización de respuestas aprobadas

El chatbot SHALL priorizar una respuesta expresamente aprobada cuando una consulta coincida con una pregunta o situación que tenga tal respuesta en las fuentes de conocimiento administradas y la respuesta esté autorizada para el rol del usuario, conservando su significado y sin sustituirla por una respuesta contradictoria generada por el modelo (regla 8 de CU-12). Cuando la respuesta aprobada no está autorizada para el rol del usuario, el chatbot MUST NO utilizarla ni revelarla (regla 7 de CU-12). Este comportamiento complementa, sin reemplazarlos, los requisitos "Consulta sin información suficiente" y "Rechazo de mutaciones, corrección y calificación" de esta capacidad.

#### Scenario: Consulta que coincide con una respuesta aprobada

- **GIVEN** que existe una respuesta aprobada en una fuente de conocimiento administrada, autorizada para el rol del usuario, y la consulta coincide con esa pregunta o situación
- **WHEN** el chatbot responde
- **THEN** prioriza la respuesta aprobada
- **AND** conserva su significado en la respuesta (regla 8 de CU-12)

#### Scenario: El modelo no sustituye la respuesta aprobada

- **GIVEN** que el conocimiento general del modelo contradice una respuesta aprobada recuperada
- **WHEN** el chatbot genera la respuesta
- **THEN** prevalece la respuesta aprobada
- **AND** no se sustituye por una respuesta contradictoria del modelo (regla 8 de CU-12)

#### Scenario: Respuesta aprobada no autorizada para el rol

- **GIVEN** que una respuesta aprobada está dirigida a un rol distinto del del usuario autenticado
- **WHEN** el usuario envía una consulta que coincidiría con esa respuesta
- **THEN** el chatbot no la utiliza ni revela
- **AND** responde solo con conocimiento autorizado para su rol (regla 7 de CU-12)

### Requirement: Recuperación de conocimiento filtrada por rol

El chatbot SHALL recuperar fragmentos de las fuentes de conocimiento administradas únicamente cuando estén autorizados para el rol del usuario autenticado (regla 7 de CU-12). La identidad y el rol del usuario MUST obtenerse exclusivamente de la sesión activa en el backend, nunca de parámetros proporcionados al modelo ni de instrucciones que el modelo pueda interpretar de manera ambigua (regla 16 de CU-11). Una guía, respuesta u otro contenido dirigido a roles específicos MUST permanecer fuera del alcance de usuarios de roles no autorizados: el chatbot MUST NO recuperar, utilizar ni revelar dicho contenido. Cuando una consulta solo podría responderse con contenido no autorizado para el rol del usuario, el chatbot informa que no puede proporcionar esa información sin revelar su contenido.

#### Scenario: Contenido de un rol no se revela a otros roles

- **GIVEN** que una fuente de conocimiento administrada está dirigida solo a Profesores o Administradores y un Estudiante envía una consulta cuya respuesta estaría cubierta por esa fuente
- **WHEN** el chatbot recupera conocimiento para responder
- **THEN** no recupera ni utiliza los fragmentos de esa fuente
- **AND** no revela información restringida a otros roles (regla 7 de CU-12)

#### Scenario: Contenido autorizado para el rol del usuario

- **GIVEN** que una fuente de conocimiento administrada incluye dentro de sus roles destino al rol del usuario autenticado
- **WHEN** el usuario envía una consulta pertinente
- **THEN** el chatbot recupera los fragmentos relevantes de esa fuente
- **AND** los utiliza dentro del alcance permitido para su rol (regla 7 de CU-12)

#### Scenario: Rol tomado de la sesión, no del modelo

- **GIVEN** que un usuario intenta inducir un rol distinto del suyo mediante los parámetros o el texto de su consulta
- **WHEN** la herramienta de recuperación de conocimiento procesa la solicitud
- **THEN** valida la sesión activa en el backend
- **AND** aplica el rol real del usuario, sin confiar en parámetros externos (regla 16 de CU-11)

## MODIFIED Requirements

### Requirement: Respuesta anclada a la documentación de la plataforma

Cuando la consulta se relaciona con el funcionamiento de la plataforma (paso 6), el chatbot SHALL utilizar principalmente las fuentes de conocimiento administradas por el Administrador (capacidad `chatbot-knowledge-sources`: guías de uso, instrucciones por rol, documentación de funcionalidades y reglas de negocio, preguntas frecuentes y respuestas aprobadas) para responder. Los conocimientos generales del modelo MAY utilizarse como complemento únicamente cuando no contradigan las fuentes administradas. Los conocimientos generales del modelo MUST NOT utilizarse para inventar funcionalidades o reglas de la aplicación (regla 7 de CU-11 y regla 9 de CU-12). El chatbot MUST NOT inventar ni presentar como confirmados datos de la plataforma que no haya podido verificar a través de fuentes autorizadas (regla 5 de CU-11). Cuando las fuentes administradas establezcan una regla específica de la plataforma, esa información prevalece sobre el conocimiento general del modelo; ante información contradictoria o insuficiente, el chatbot reconoce la limitación en lugar de inventar una regla (regla 9 de CU-12). Cuando el sistema no dispone de fuentes administradas activas pertinentes y autorizadas para el rol, el chatbot aplica el comportamiento del requisito "Consulta sin información suficiente" sin presentar conocimiento general como regla confirmada de la plataforma.
(Previously: la referencia principal era la documentación del repositorio del proyecto — `AGENTS.md`, `README.md` y `casos_de_uso.md` —; ahora pasa a ser las fuentes de conocimiento administradas por el Administrador.)

#### Scenario: Consulta sobre funcionamiento de la plataforma

- **GIVEN** que un usuario autenticado pregunta cómo funciona una funcionalidad descrita en una fuente de conocimiento administrada activa y autorizada para su rol
- **WHEN** el chatbot responde
- **THEN** la respuesta se basa principalmente en las fuentes de conocimiento administradas
- **AND** no inventa funcionalidades ni reglas que no estén respaldadas por fuentes autorizadas

#### Scenario: Conocimiento general solo como complemento

- **GIVEN** que una consulta puede complementarse con información general sin contradecir las fuentes administradas
- **WHEN** el chatbot responde
- **THEN** el uso de conocimientos generales es estrictamente complementario
- **AND** no sustituye ni contradice las fuentes administradas ni los datos verificados del sistema

#### Scenario: Fuente administrada prevalece sobre el conocimiento general

- **GIVEN** que una fuente de conocimiento administrada activa y autorizada para el rol establece una regla específica de la plataforma que contradice el conocimiento general del modelo
- **WHEN** el chatbot responde a una consulta pertinente
- **THEN** la respuesta refleja la regla establecida por la fuente
- **AND** no la sustituye por la versión contradictoria del modelo (regla 9 de CU-12)
- **AND** si detecta contradicción no salvable o información insuficiente, reconoce la limitación

#### Scenario: Sin fuentes pertinentes disponibles

- **GIVEN** que no existen fuentes de conocimiento administradas activas pertinentes para la consulta o autorizadas para el rol del usuario
- **WHEN** el chatbot responde
- **THEN** aplica el comportamiento de "Consulta sin información suficiente"
- **AND** no presenta conocimiento general como regla confirmada de la plataforma

### Requirement: Integración con arquitectura existente y endpoints

La implementación del chatbot SHALL seguir las capas establecidas: `routes → services → models` (regla backend). SHALL crear un blueprint nuevo `backend/blueprints/chat.py` registrado en `app.py`, un servicio nuevo `backend/services/chat_service.py` (orquestación del agente y herramientas de solo lectura delegando en los `services/` existentes), modelos nuevos de historial en `backend/models/` y migración incremental en `backend/migrations/` (post `0007`). No SHALL modificar contratos, endpoints ni comportamiento de CU-01 a CU-10 existentes. El frontend SHALL implementar la feature en `frontend/src/features/chatbot/` con página `/chat` enlazada desde el sidebar para los tres roles, utilizando el design system (`src/ui/`, tokens, sin colores hardcodeados), y consumiendo el backend a través de `src/api/client.js`. Las dependencias `langchain` y `langchain-ollama` SHALL añadirse a `backend/requirements.txt` con versiones fijadas. La integración con las fuentes de conocimiento administradas (capacidad `chatbot-knowledge-sources`) SHALL realizarse mediante una herramienta de solo lectura incorporada en `build_tools(current_user)` de `backend/services/chat_service.py`, que delega en el servicio de conocimiento del backend y recupera fragmentos filtrados por el rol del usuario tomado de la sesión activa. Esta herramienta MUST preservar la garantía de solo lectura del agente: ninguna herramienta expuesta al agente MAY realizar operaciones de escritura, modificación o eliminación, ni en los datos funcionales de la plataforma ni en las fuentes de conocimiento.
(Previously: no contemplaba la integración con fuentes de conocimiento administradas ni la herramienta de recuperación en `build_tools`.)

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

#### Scenario: Herramienta de recuperación de conocimiento integrada en build_tools

- **GIVEN** que se implementa la integración con las fuentes de conocimiento administradas
- **WHEN** se construyen las herramientas del agente en `build_tools(current_user)`
- **THEN** la herramienta de recuperación es de solo lectura y delega en los `services/` del backend
- **AND** obtiene identidad y rol del usuario desde la sesión activa de Flask, nunca desde parámetros del modelo
- **AND** ninguna herramienta expuesta al agente realiza operaciones de escritura (garantía de solo lectura de CU-11 preservada)

## RENAMED Requirements

### Requirement: Respuesta anclada a la documentación de la plataforma → Respuesta anclada a fuentes de conocimiento administradas

(Reason: la referencia principal del chatbot deja de ser la documentación del repositorio del proyecto y pasa a ser las fuentes de conocimiento administradas por el Administrador, conforme al objetivo y a las reglas de CU-12.)
(Migration: las referencias al nombre anterior del requisito en tests, documentación y artefactos de UI deben actualizarse al nuevo nombre al archivar el cambio.)
