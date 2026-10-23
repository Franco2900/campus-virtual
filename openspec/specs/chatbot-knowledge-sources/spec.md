# chatbot-knowledge-sources Specification

## Purpose
Permitir que el Administrador gestione las fuentes de conocimiento autorizadas del chatbot (carga, validación, procesamiento, listado y eliminación de documentos y respuestas aprobadas), y que el chatbot utilice ese conocimiento mediante recuperación RAG scopeada por el rol del usuario, priorizando las respuestas aprobadas, respetando los permisos de acceso y preservando la garantía de solo lectura de la plataforma (CU-12).

## Requirements

### Requirement: Gestión de fuentes exclusiva del Administrador

El sistema SHALL permitir listar, cargar y eliminar fuentes de conocimiento del chatbot únicamente a usuarios autenticados con rol Administrador (regla 1 de CU-12). Un usuario sin sesión activa MUST recibir HTTP 401 al acceder a los endpoints de gestión o a la pantalla de gestión. Un usuario autenticado con un rol distinto de Administrador MUST recibir HTTP 403 y un mensaje que informe que la operación requiere permisos de Administrador (A3). Las verificaciones de permisos MUST realizarse en el backend, tomando el rol exclusivamente de la sesión activa (regla 2 de CU-12). La interfaz de gestión SHALL estar habilitada únicamente para el Administrador.

#### Scenario: Acceso sin sesión a los endpoints de gestión

- **GIVEN** que una persona no ha iniciado sesión
- **WHEN** intenta listar, cargar o eliminar fuentes mediante los endpoints de gestión
- **THEN** el sistema responde HTTP 401
- **AND** no se realiza ninguna operación sobre las fuentes

#### Scenario: Usuario sin rol Administrador intenta gestionar fuentes (A3)

- **GIVEN** que un usuario autenticado con rol Estudiante o Profesor intenta acceder a la sección de gestión o ejecutar una operación sobre fuentes
- **WHEN** el sistema procesa la solicitud
- **THEN** responde HTTP 403
- **AND** informa que la operación requiere permisos de Administrador

#### Scenario: Administrador accede a la gestión de fuentes

- **GIVEN** que un usuario autenticado con rol Administrador tiene sesión activa
- **WHEN** accede a la sección de gestión de fuentes de conocimiento
- **THEN** el sistema verifica el rol en el backend
- **AND** habilita las operaciones de listado, carga y eliminación

### Requirement: Carga de fuentes de conocimiento

El sistema SHALL permitir al Administrador cargar un archivo como fuente de conocimiento mediante `POST /api/knowledge/sources`, acompañado de la información descriptiva necesaria: nombre, descripción o propósito, roles destino (Estudiante, Profesor y/o Administrador) y tipo de fuente (`document` para guías y documentación; `approved_answer` para preguntas o situaciones con una respuesta expresamente aprobada) (A1 pasos 1-3; reglas 3 y 6 de CU-12). El sistema SHALL admitir los formatos `.md` y `.txt` y aplicar el límite de tamaño definido por la configuración del sistema (reglas 4 y 15 de CU-12; los valores exactos se fijan en el diseño técnico). El contenido admitido comprende guías de uso de la plataforma, instrucciones para los distintos roles, documentación de funcionalidades y reglas de negocio, preguntas frecuentes con sus respuestas aprobadas, y preguntas o situaciones determinadas para las que se haya definido una respuesta que el chatbot deba proporcionar (regla 3 de CU-12). El sistema SHALL registrar la información necesaria para identificar la fuente y determinar a qué roles y propósito se asocia (regla 6 de CU-12). En caso de éxito, el sistema SHALL responder HTTP 201 con la fuente registrada e informa al Administrador que la operación se registró (A1 paso 8).

#### Scenario: Carga exitosa de una fuente con metadatos

- **GIVEN** que el Administrador selecciona un archivo `.md` o `.txt` e ingresa nombre, descripción o propósito, roles destino y tipo de fuente
- **WHEN** envía la carga con información válida
- **THEN** el sistema responde HTTP 201 con la fuente registrada
- **AND** la fuente queda identificable por su nombre, propósito, roles destino y tipo (regla 6 de CU-12)

#### Scenario: Formato de archivo no admitido (A4)

- **GIVEN** que el Administrador intenta cargar un archivo con una extensión distinta de `.md` o `.txt`
- **WHEN** el sistema valida la carga
- **THEN** responde HTTP 400 indicando el motivo del rechazo
- **AND** el archivo no se incorpora a las fuentes de conocimiento del chatbot (regla 4 de CU-12)

#### Scenario: Archivo que excede el límite de tamaño (A4)

- **GIVEN** que el Administrador intenta cargar un archivo que supera el límite de tamaño definido por el sistema
- **WHEN** el sistema valida la carga
- **THEN** responde HTTP 400 indicando el motivo del rechazo
- **AND** el archivo no se incorpora a las fuentes de conocimiento del chatbot (reglas 4 y 15 de CU-12)

#### Scenario: Fuente dirigida a varios roles

- **GIVEN** que el Administrador carga una fuente con roles destino "Profesor" y "Administrador"
- **WHEN** la carga se registra correctamente
- **THEN** la fuente queda asociada a ambos roles destino
- **AND** su propósito queda registrado para identificarla (regla 6 de CU-12)

### Requirement: Procesamiento, indexado y activación de fuentes

Tras almacenar un archivo validado, el sistema SHALL procesar su contenido para incorporarlo al mecanismo de recuperación del chatbot: segmentación del contenido e indexado en el almacén vectorial local (ChromaDB) con embeddings producidos por Ollama (modelo `nomic-embed-text`, configurable por entorno; decisiones aprobadas en la propuesta del cambio). Una fuente con `source_type='approved_answer'` SHALL parsearse a fragmentos individuales marcados con prioridad alta para su utilización en la recuperación (regla 8 de CU-12). El sistema SHALL reflejar el estado de cada archivo durante su ciclo de vida: `processing` mientras se procesa, `active` cuando el procesamiento finaliza correctamente y `error` cuando falla (reglas 5 y 13 de CU-12). Una fuente solo MUST utilizarse como conocimiento disponible por el chatbot después de que su carga y procesamiento hayan finalizado correctamente, es decir, cuando su estado es `active` (regla 5 de CU-12). Una fuente en estado `processing` o `error` MUST quedar excluida de la recuperación del chatbot. Una vez completado correctamente el procesamiento, el sistema habilita la fuente para su utilización por el chatbot e informa al Administrador que la operación finalizó correctamente (A1 pasos 4-7 y 8).

#### Scenario: Procesamiento correcto y activación

- **GIVEN** que el Administrador cargó un archivo válido
- **WHEN** el sistema valida, segmenta e indexa su contenido sin errores
- **THEN** la fuente transita de `processing` a `active`
- **AND** su contenido queda disponible en la recuperación del chatbot para los roles autorizados (A1 pasos 4-7)

#### Scenario: Fuente de respuestas aprobadas procesada

- **GIVEN** que el Administrador cargó una fuente con `source_type='approved_answer'`
- **WHEN** el sistema procesa su contenido
- **THEN** registra sus fragmentos con prioridad alta para la recuperación
- **AND** la fuente queda `active` al finalizar correctamente (regla 8 de CU-12)

#### Scenario: Fallo en el procesamiento (A5)

- **GIVEN** que se produce un error durante el procesamiento del contenido (por ejemplo, el servicio de embeddings no está disponible)
- **WHEN** el sistema detecta el fallo
- **THEN** informa que no pudo completar la operación
- **AND** la fuente queda en estado `error`
- **AND** el sistema evita presentar como disponible una fuente cuyo procesamiento no haya finalizado correctamente (reglas 5 y 13 de CU-12)

#### Scenario: Fuente no activa no es recuperable

- **GIVEN** que existen fuentes en estado `processing` o `error`
- **WHEN** un usuario envía una consulta al chatbot
- **THEN** el chatbot no utiliza el contenido de esas fuentes
- **AND** únicamente recupera conocimiento de fuentes en estado `active` (reglas 5 y 13 de CU-12)

### Requirement: Rechazo de archivos no válidos

Cuando el archivo no cumple los requisitos de formato o tamaño, está dañado o no puede procesarse, el sistema MUST rechazar la carga, informar el motivo cuando pueda determinarlo (HTTP 400) y MUST NO incorporar el archivo a las fuentes activas del chatbot (A4). El sistema no MUST registrar como disponible una fuente cuya carga o validación haya sido rechazada.

#### Scenario: Archivo dañado o no procesable (A4)

- **GIVEN** que el Administrador intenta cargar un archivo dañado o cuyo contenido no puede procesarse
- **WHEN** el sistema valida o procesa el archivo
- **THEN** rechaza la operación e informa el motivo cuando puede determinarlo
- **AND** el archivo no se incorpora a las fuentes activas del chatbot (A4 pasos 1-4)

#### Scenario: Rechazo no deja fuentes disponibles

- **GIVEN** que una carga fue rechazada por inválida
- **WHEN** un usuario consulta al chatbot
- **THEN** el contenido del archivo rechazado no se utiliza
- **AND** el chatbot no lo presenta como fuente vigente

### Requirement: Listado e identificación de fuentes

El sistema SHALL permitir al Administrador listar las fuentes de conocimiento registradas mediante `GET /api/knowledge/sources`, mostrando para cada una la información que permite identificarla: nombre, descripción o propósito, roles destino, tipo (`document` o `approved_answer`) y estado (`processing`, `active` o `error`) (flujo principal pasos 3-4; regla 6 de CU-12). La pantalla de gestión SHALL mostrar ese listado al Administrador.

#### Scenario: Listado de fuentes con metadata y estado

- **GIVEN** que el Administrador accede a la sección de gestión
- **WHEN** el sistema muestra las fuentes registradas
- **THEN** cada fuente aparece con su nombre, descripción o propósito, roles destino, tipo y estado
- **AND** el Administrador puede identificar cada fuente y determinar su disponibilidad (reglas 6 y 13 de CU-12)

#### Scenario: Listado con fuentes en distintos estados

- **GIVEN** que existen fuentes en estados `processing`, `active` y `error`
- **WHEN** el Administrador lista las fuentes
- **THEN** el estado de cada fuente se muestra correctamente
- **AND** distingue las fuentes utilizables por el chatbot de las que no lo están

### Requirement: Eliminación de fuentes

El sistema SHALL permitir al Administrador eliminar una fuente registrada mediante `DELETE /api/knowledge/sources/<id>`. La interfaz SHALL mostrar la información que identifica la fuente seleccionada y SHALL solicitar confirmación previa antes de ejecutar la eliminación (A2 pasos 1-4). Al confirmar, el sistema MUST retirar la fuente del mecanismo de recuperación activo del chatbot, del almacenamiento del archivo y de su registro en la base de datos, de manera que deje de utilizarse como fuente vigente en futuras respuestas (reglas 11 y 13 de CU-12; A2 paso 6). El sistema informa que la fuente fue eliminada correctamente (A2 paso 7). Si la fuente no existe, el sistema responde HTTP 404.

#### Scenario: Eliminación confirmada (A2)

- **GIVEN** que el Administrador selecciona una fuente registrada y solicita eliminarla
- **WHEN** confirma la operación en el diálogo de confirmación
- **THEN** el sistema retira la fuente del mecanismo de recuperación del chatbot, del almacenamiento del archivo y de su registro
- **AND** informa que la fuente fue eliminada correctamente (A2 pasos 5-7)

#### Scenario: Consulta basada en una fuente eliminada (A7)

- **GIVEN** que una fuente de conocimiento fue eliminada y un usuario realiza una consulta cuyo contenido estaba cubierto por esa fuente
- **WHEN** el chatbot procesa la consulta
- **THEN** consulta las fuentes de conocimiento que permanecen disponibles
- **AND** responde utilizando la información vigente que puede verificar
- **AND** si no dispone de información suficiente, reconoce la limitación y NO presenta el contenido eliminado como una fuente vigente (A7)

#### Scenario: Eliminación de una fuente inexistente

- **GIVEN** que el Administrador solicita eliminar una fuente que no existe
- **WHEN** el sistema procesa la solicitud
- **THEN** responde HTTP 404
- **AND** no se elimina ninguna fuente

### Requirement: Cancelación de la eliminación

Al solicitar eliminar una fuente, el sistema MUST solicitar confirmación. Cuando el Administrador cancela la operación, el sistema MUST conservar el archivo y mantener su estado anterior (A6). Una fuente que estaba `active` antes de la cancelación MUST seguir siendo utilizable por el chatbot.

#### Scenario: Cancelación conserva la fuente (A6)

- **GIVEN** que el Administrador abrió el diálogo de confirmación para eliminar una fuente
- **WHEN** cancela la operación antes de confirmarla
- **THEN** la fuente se conserva íntegra
- **AND** su estado anterior se mantiene sin cambios (A6 pasos 1-4)

### Requirement: La gestión de fuentes no afecta el historial de conversaciones

La eliminación de una fuente de conocimiento MUST NO eliminar ni modificar el historial de conversaciones de los usuarios en el que su contenido se hubiera mencionado o utilizado (regla 12 de CU-12). La gestión de fuentes es una operación administrativa independiente del historial de conversaciones, que permanece asociado a cada usuario según lo definido en la capacidad `chatbot-assistant`.

#### Scenario: Fuente utilizada en conversaciones previas es eliminada

- **GIVEN** que una fuente de conocimiento fue utilizada por el chatbot en conversaciones previas de uno o varios usuarios
- **WHEN** el Administrador elimina la fuente
- **THEN** el historial de conversaciones permanece intacto
- **AND** los mensajes previos no se eliminan ni se reescriben (regla 12 de CU-12)

### Requirement: Recuperación de conocimiento scopeada por rol

El chatbot SHALL utilizar únicamente la información pertinente y autorizada para el rol del usuario autenticado al recuperar fragmentos de las fuentes de conocimiento (regla 7 de CU-12). El rol del usuario MUST obtenerse desde la sesión activa en el backend, nunca de parámetros proporcionados al modelo. Cuando una fuente define roles destino, su contenido MUST filtrarse de manera que solo sea recuperable para usuarios de esos roles: una guía, respuesta u otro contenido dirigido a un rol no MUST revelarse a usuarios de los demás roles (regla 7 de CU-12). Cuando una fuente no define roles destino, su contenido aplica a todos los usuarios autenticados. Los controles de acceso de la plataforma siguen aplicando con independencia del contenido recuperado (regla 10 de CU-12).

#### Scenario: Contenido de un rol no se revela a otros roles

- **GIVEN** que existe una fuente `active` dirigida solo al rol Profesor y un Estudiante envía una consulta cuya respuesta estaría cubierta por esa fuente
- **WHEN** el chatbot recupera conocimiento para responder
- **THEN** no recupera ni utiliza los fragmentos de esa fuente
- **AND** no revela información restringida a otros roles (regla 7 de CU-12)

#### Scenario: Contenido autorizado para el rol del usuario

- **GIVEN** que existe una fuente `active` cuyos roles destino incluyen al rol del usuario autenticado
- **WHEN** el usuario envía una consulta pertinente
- **THEN** el chatbot recupera los fragmentos relevantes de esa fuente
- **AND** los utiliza dentro del alcance permitido para su rol (regla 7 de CU-12)

#### Scenario: Solicitud de contenido restringido

- **GIVEN** que un usuario solicita información que solo está cubierta por fuentes no autorizadas para su rol
- **WHEN** el chatbot procesa la solicitud
- **THEN** informa que no puede proporcionar esa información
- **AND** no revela el contenido de las fuentes restringidas

### Requirement: Priorización de respuestas aprobadas

Cuando una consulta coincide con una pregunta o situación que tiene una respuesta expresamente aprobada en una fuente `approved_answer` autorizada para el rol del usuario, el chatbot SHALL priorizar esa respuesta y conservar su significado, sin sustituirla por una respuesta contradictoria generada por el modelo (regla 8 de CU-12). Cuando la respuesta aprobada no está autorizada para el rol del usuario, el chatbot MUST NOT utilizarla ni revelarla (reglas 7 y 8 de CU-12).

#### Scenario: Consulta que coincide con una respuesta aprobada

- **GIVEN** que una fuente `approved_answer` `active` contiene una respuesta aprobada autorizada para el rol del usuario y la consulta coincide con esa pregunta o situación
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
- **AND** responde solo con conocimiento autorizado para su rol (reglas 7 y 8 de CU-12)

### Requirement: Prioridad de las fuentes administradas sobre el conocimiento general

Cuando las fuentes de conocimiento establezcan una regla específica de la plataforma, el chatbot SHALL priorizar esa información frente a sus conocimientos generales (regla 9 de CU-12). Si el chatbot encuentra información contradictoria o insuficiente, MUST reconocer la limitación en lugar de inventar una regla (regla 9 de CU-12). Los conocimientos generales del modelo MAY utilizarse como complemento únicamente cuando no contradigan las fuentes administradas.

#### Scenario: La fuente prevalece ante contradicción

- **GIVEN** que una fuente `active` autorizada para el rol del usuario establece una regla específica de la plataforma que contradice el conocimiento general del modelo
- **WHEN** el chatbot responde a una consulta pertinente
- **THEN** la respuesta refleja la regla establecida por la fuente
- **AND** no la sustituye por la versión contradictoria del conocimiento general (regla 9 de CU-12)

#### Scenario: Contradicción o insuficiencia reconoce la limitación

- **GIVEN** que las fuentes de conocimiento disponibles contienen información contradictoria entre sí o insuficiente para responder con certeza la consulta
- **WHEN** el chatbot procesa la consulta
- **THEN** reconoce la limitación
- **AND** no inventa una regla de la plataforma para cubrir la falta de información (regla 9 de CU-12)

### Requirement: Las fuentes no otorgan permisos ni habilitan mutaciones

El contenido de las fuentes de conocimiento MUST NO otorgar permisos adicionales al usuario ni permitir omitir los controles de acceso definidos en la plataforma (regla 10 de CU-12): la autorización de cada operación del chatbot se evalúa según el rol del usuario en el backend, con independencia del contenido recuperado. La gestión de fuentes y su utilización por el chatbot MUST NO habilitar la creación, modificación o eliminación de datos funcionales de la plataforma (usuarios, cursos, inscripciones, tareas, entregas, calificaciones) mediante el chatbot (regla 14 de CU-12). El chatbot se mantiene de solo lectura, en consonancia con la capacidad `chatbot-assistant`.

#### Scenario: El contenido de una fuente no modifica los controles de acceso

- **GIVEN** que el contenido de una fuente de conocimiento incluye instrucciones que, de seguirse, mostrarían datos de otros usuarios u omitirían controles de acceso
- **WHEN** el chatbot procesa una consulta que recupera ese contenido
- **THEN** el sistema respeta los controles de acceso definidos en el backend según el rol del usuario
- **AND** el contenido de la fuente no otorga permisos adicionales (regla 10 de CU-12)

#### Scenario: La gestión de fuentes no habilita mutaciones vía chatbot

- **GIVEN** que un usuario solicita mediante el chatbot crear, modificar o eliminar datos funcionales, citando o apoyándose en el contenido de una fuente de conocimiento
- **WHEN** el chatbot procesa la solicitud
- **THEN** informa que no puede ejecutar esa operación
- **AND** no se crea, modifica ni elimina ningún dato funcional de la plataforma (regla 14 de CU-12)
