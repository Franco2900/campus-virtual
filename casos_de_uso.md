# Casos de uso — Campus Virtual

**Tema:** Campus Virtual.
**Grupo:** 12.

## Integrantes

| Apellido y nombre | Email | GitHub |
|-------------------|-------|--------|
| Figueroa, Franco Ariel | franco2900@gmail.com | Franco2900 |

## Stack tecnológico

| Área | Tecnología | Versión |
|------|-----------|---------|
| Backend | Python + Flask | 3.14.6 / PENDIENTE DE DEFINIR (Flask) |
| Frontend | React + Vite | PENDIENTE DE DEFINIR (React / Vite) |
| Runtime frontend | Node | v24.19.0 |
| Base de datos | SQLite | PENDIENTE DE DEFINIR |
| ORM | SQLAlchemy | PENDIENTE DE DEFINIR |
| Chatbot | LangChain + Ollama (local) | PENDIENTE DE DEFINIR |

## Actores del sistema

- **Usuario:** persona que utiliza el sistema. Puede registrarse y autenticarse.
- **Estudiante:** usuario con rol Estudiante. Puede inscribirse en cursos, entregar tareas y consultar sus calificaciones.
- **Profesor:** usuario con rol Profesor. Puede gestionar tareas, gestionar inscripciones y corregir tareas de sus cursos.
- **Administrador:** usuario con rol Administrador. Puede gestionar cursos, usuarios e inscripciones y filtrar usuarios.

### Reglas generales de roles

- Cada usuario tiene exactamente un rol a la vez.
- Los roles son mutuamente excluyentes.
- Los usuarios nuevos reciben inicialmente el rol Estudiante.
- El rol de Profesor es asignado por un Administrador.

## Resumen de casos de uso

| ID | Nombre | Actor principal |
|----|--------|-----------------|
| CU-01 | Registrarse | Usuario no registrado |
| CU-02 | Autenticarse | Usuario |
| CU-03 | Gestionar cursos | Administrador |
| CU-04 | Gestionar usuarios | Administrador |
| CU-05 | Gestionar inscripciones | Administrador / Profesor |
| CU-06 | Gestionar tareas | Profesor |
| CU-07 | Entregar tarea | Estudiante |
| CU-08 | Corregir tarea | Profesor |
| CU-09 | Consultar calificaciones | Profesor / Estudiante |
| CU-10 | Filtrar usuarios | Administrador |
| CU-11 | Utilizar chatbot de asistencia | Usuario autenticado (Estudiante / Profesor / Administrador) |

---

## CU-01 — Registrarse

**Actor principal:** Usuario no registrado.

**Objetivo:** permitir que un usuario cree una cuenta en el sistema.

**Precondiciones:**
- El usuario no posee una cuenta registrada.
- El correo electrónico no se encuentra asociado a otra cuenta.

**Flujo principal:**
1. El usuario selecciona la opción Registrarse.
2. El sistema solicita los datos necesarios para crear la cuenta.
3. El usuario ingresa nombre, apellido, correo electrónico y contraseña.
4. El sistema verifica que el correo electrónico no se encuentre registrado.
5. El sistema valida los datos ingresados.
6. El sistema crea la cuenta.
7. El sistema asigna inicialmente el rol Estudiante.
8. El sistema confirma el registro.

**Postcondiciones:**
- La cuenta del usuario queda registrada.
- El usuario posee el rol Estudiante.
- El correo electrónico queda asociado de forma única a la cuenta.

**Reglas:**
- El correo electrónico funciona como identificador único de la cuenta.
- Un usuario solo puede poseer un rol a la vez.

---

## CU-02 — Autenticarse

**Actor principal:** Usuario.

**Objetivo:** permitir que un usuario inicie y cierre sesión y pueda recuperar el acceso a su cuenta.

**Precondiciones:**
- El usuario posee una cuenta registrada.

**Flujo principal — Inicio de sesión:**
1. El usuario ingresa su correo electrónico y contraseña.
2. El sistema verifica las credenciales.
3. Si las credenciales son correctas, el sistema inicia la sesión.
4. El sistema identifica el rol del usuario.
5. El sistema permite acceder a las funcionalidades correspondientes a dicho rol.

**Flujo alternativo A1 — Credenciales incorrectas:**
1. El sistema informa que el correo electrónico o la contraseña son incorrectos.
2. El usuario puede volver a ingresar sus credenciales.

**Flujo alternativo A2 — Recuperación de contraseña:**
1. El usuario selecciona la opción de recuperación de contraseña.
2. El sistema solicita el correo electrónico asociado a la cuenta.
3. El usuario ingresa su correo electrónico.
4. El sistema verifica que la cuenta exista.
5. El sistema envía un enlace de recuperación al correo electrónico registrado.
6. El usuario accede al enlace y establece una nueva contraseña.

**Flujo alternativo A3 — Cerrar sesión:**
1. El usuario selecciona la opción Cerrar sesión.
2. El sistema finaliza la sesión activa.

**Reglas:**
- Cada usuario posee un único rol.
- El acceso a las funcionalidades depende del rol del usuario.

---

## CU-03 — Gestionar cursos

**Actor principal:** Administrador.

**Objetivo:** permitir al Administrador crear, consultar, modificar y desactivar cursos.

**Precondiciones:**
- El Administrador inició sesión.
- El usuario posee el rol Administrador.

**Flujo principal:**
1. El Administrador accede a la gestión de cursos.
2. El sistema muestra los cursos registrados.
3. El Administrador selecciona una operación: crear, consultar, modificar o desactivar.
4. Para crear un curso, el Administrador ingresa los datos correspondientes.
5. El sistema valida los datos.
6. El sistema registra el nuevo curso.
7. Para consultar un curso, el sistema muestra la información correspondiente.
8. Para modificar un curso, el Administrador selecciona el curso e ingresa los nuevos datos.
9. El sistema valida y guarda las modificaciones.
10. Para desactivar un curso, el Administrador selecciona el curso.
11. El sistema cambia el estado del curso a inactivo.

**Reglas:**
- Un curso puede tener múltiples estudiantes.
- Un curso puede tener múltiples profesores.
- Un curso puede encontrarse activo o inactivo.
- Los cursos inactivos no deben tratarse como cursos activos.

---

## CU-04 — Gestionar usuarios

**Actor principal:** Administrador.

**Objetivo:** permitir al Administrador gestionar las cuentas de usuarios y sus roles.

**Precondiciones:**
- El Administrador inició sesión.
- El usuario posee el rol Administrador.

**Flujo principal:**
1. El Administrador accede a la gestión de usuarios.
2. El sistema muestra los usuarios registrados.
3. El Administrador selecciona un usuario.
4. El sistema muestra la información correspondiente.
5. El Administrador puede gestionar los datos y el rol del usuario.
6. El sistema valida la operación.
7. El sistema guarda los cambios.

**Flujo alternativo A1 — Asignar rol de Profesor:**
1. El Administrador selecciona un usuario.
2. Selecciona la opción para asignar el rol Profesor.
3. El sistema solicita confirmación.
4. El Administrador confirma.
5. El sistema asigna el rol Profesor.
6. El usuario deja de poseer el rol anterior, manteniendo exactamente un rol.

**Flujo alternativo A2 — Cambiar rol de Profesor a Estudiante:**
1. El Administrador selecciona un usuario que posee el rol Profesor.
2. Selecciona la opción para cambiar su rol a Estudiante.
3. El sistema solicita confirmación.
4. El Administrador confirma.
5. El sistema asigna el rol Estudiante.

**Reglas:**
- Cada usuario debe poseer exactamente un rol.
- Los roles son mutuamente excluyentes.
- La asignación del rol Profesor corresponde al Administrador.
- Un usuario no puede conservar simultáneamente dos o más roles.

---

## CU-05 — Gestionar inscripciones

**Actores principales:** Administrador, Profesor.

**Objetivo:** permitir gestionar las inscripciones de estudiantes en los cursos.

**Precondiciones:**
- El usuario que realiza la operación inició sesión.
- El usuario posee el rol Administrador o Profesor.
- El curso existe y se encuentra disponible para la operación.

**Flujo principal:**
1. El Administrador o Profesor accede a la gestión de inscripciones.
2. El sistema muestra los cursos correspondientes.
3. El usuario selecciona un curso.
4. El sistema muestra los estudiantes y sus inscripciones.
5. El usuario selecciona la operación correspondiente.
6. El usuario registra, modifica o elimina una inscripción.
7. El sistema valida la operación.
8. El sistema guarda la inscripción actualizada.
9. El sistema muestra el resultado de la operación.

**Reglas:**
- Las inscripciones se realizan sobre cursos existentes.
- Un profesor solo puede inscribir estudiantes en los cursos en los que trabaja.
- Un estudiante puede estar inscripto en los cursos que correspondan.
- La gestión de inscripciones no genera notificaciones automáticas por correo electrónico.

---

## CU-06 — Gestionar tareas

**Actor principal:** Profesor.

**Objetivo:** permitir al Profesor crear, consultar, modificar y desactivar tareas.

**Precondiciones:**
- El Profesor inició sesión.
- El usuario posee el rol Profesor.
- El Profesor está asociado al curso correspondiente.

**Flujo principal:**
1. El Profesor accede a la gestión de tareas.
2. El sistema muestra los cursos correspondientes.
3. El Profesor selecciona un curso.
4. El sistema muestra las tareas existentes.
5. El Profesor selecciona una operación: crear, consultar, modificar o desactivar.
6. Para crear una tarea, el Profesor ingresa los datos correspondientes.
7. El sistema valida los datos.
8. El sistema registra la tarea.
9. Para consultar una tarea, el sistema muestra la información correspondiente.
10. Para modificar una tarea, el Profesor selecciona la tarea e ingresa los nuevos datos.
11. El sistema valida y guarda las modificaciones.
12. Para desactivar una tarea, el Profesor selecciona la tarea.
13. El sistema cambia el estado de la tarea a inactivo.

**Flujo alternativo A1 — Modificación de fecha límite:**
1. El Profesor selecciona una tarea.
2. Modifica la fecha límite.
3. El sistema valida la nueva fecha.
4. El sistema guarda la modificación.

**Reglas:**
- Las tareas pertenecen a un curso.
- Una tarea puede encontrarse activa o inactiva.
- Las modificaciones de tareas no generan notificaciones automáticas por correo electrónico.

---

## CU-07 — Entregar tarea

**Actor principal:** Estudiante.

**Objetivo:** permitir que el Estudiante entregue, modifique o elimine una tarea antes de la fecha límite.

**Precondiciones:**
- El Estudiante inició sesión.
- El usuario posee el rol Estudiante.
- El Estudiante está inscripto en el curso correspondiente.
- La tarea se encuentra disponible.
- No se superó la fecha límite para realizar la entrega.

**Flujo principal:**
1. El Estudiante accede al curso.
2. El sistema muestra las tareas disponibles.
3. El Estudiante selecciona una tarea.
4. El Estudiante adjunta o ingresa su trabajo.
5. El sistema verifica que la entrega se encuentre dentro del plazo.
6. El sistema registra la entrega.
7. El sistema confirma la operación.

**Flujo alternativo A1 — Modificar entrega:**
1. El Estudiante selecciona una entrega existente.
2. Modifica el trabajo presentado.
3. El sistema verifica que no se haya superado la fecha límite.
4. El sistema verifica que la tarea no se haya corregido todavía.
5. El sistema actualiza la entrega.

**Flujo alternativo A2 — Eliminar entrega:**
1. El Estudiante selecciona una entrega existente.
2. Solicita eliminarla.
3. El sistema solicita confirmación.
4. El Estudiante confirma.
5. El sistema elimina la entrega.

**Reglas:**
- El Estudiante solo puede entregar tareas de cursos en los que se encuentre inscripto.
- La entrega debe realizarse antes de la fecha límite.

---

## CU-08 — Corregir tarea

**Actor principal:** Profesor.

**Objetivo:** permitir que el Profesor corrija las entregas, asigne una calificación y proporcione retroalimentación.

**Precondiciones:**
- El Profesor inició sesión.
- El usuario posee el rol Profesor.
- El Profesor está asociado al curso correspondiente.
- Existe una entrega realizada por un estudiante.

**Flujo principal:**
1. El Profesor accede al curso.
2. El sistema muestra las tareas.
3. El Profesor selecciona una tarea.
4. El sistema muestra las entregas recibidas.
5. El Profesor selecciona una entrega.
6. El sistema muestra el trabajo presentado.
7. El Profesor analiza la entrega.
8. El Profesor ingresa una calificación entre 1 y 10.
9. El Profesor ingresa la retroalimentación correspondiente.
10. De manera opcional, el Profesor puede adjuntar un archivo corregido.
11. El sistema valida la información ingresada.
12. El sistema guarda la corrección.
13. El sistema determina automáticamente si la tarea está aprobada o desaprobada según la calificación correspondiente.

**Flujo alternativo A1 — Modificación de corrección:**
1. El Profesor selecciona una entrega que ya fue corregida.
2. Modifica la calificación o la retroalimentación.
3. El sistema valida los datos.
4. El sistema guarda la nueva corrección.

**Reglas:**
- La calificación debe encontrarse entre 1 y 10.
- Cada corrección puede incluir retroalimentación.
- El archivo corregido es opcional.
- La corrección no genera una notificación automática por correo electrónico.

---

## CU-09 — Consultar calificaciones

**Actores principales:** Profesor, Estudiante.

**Objetivo:** permitir consultar las calificaciones obtenidas en las tareas.

**Precondiciones:**
- El usuario inició sesión.
- El usuario posee el rol Profesor o Estudiante.

**Flujo principal:**
1. El usuario accede a la sección de calificaciones.
2. El sistema identifica el rol del usuario.
3. Si el usuario es Estudiante, el sistema muestra sus propias calificaciones.
4. Si el usuario es Profesor, el sistema muestra las calificaciones de los estudiantes de sus cursos.
5. El sistema muestra las calificaciones correspondientes.
6. El sistema calcula el promedio según las reglas establecidas.

**Reglas:**
- El promedio se calcula mediante un promedio simple.
- Las tareas no corregidas no se incluyen en el cálculo del promedio.
- Las tareas no entregadas fuera del plazo correspondiente se contabilizan con calificación 1.
- El Estudiante solo puede consultar sus propias calificaciones.
- El Profesor puede consultar las calificaciones de los estudiantes de sus cursos.

---

## CU-10 — Filtrar usuarios

**Actor principal:** Administrador.

**Objetivo:** permitir al Administrador buscar y filtrar usuarios registrados en el sistema.

**Precondiciones:**
- El Administrador inició sesión.
- El usuario posee el rol Administrador.
- Existen usuarios registrados en el sistema.

**Flujo principal:**
1. El Administrador accede a la sección de usuarios.
2. El sistema muestra los usuarios registrados.
3. El Administrador ingresa los criterios de búsqueda o filtrado.
4. El sistema procesa los criterios ingresados.
5. El sistema muestra los usuarios que coinciden con los criterios.
6. El Administrador puede seleccionar un usuario para consultar su información.

**Flujo alternativo A1 — Sin resultados:**
1. El Administrador ingresa criterios de filtrado.
2. El sistema no encuentra usuarios que coincidan.
3. El sistema informa que no existen resultados para los criterios ingresados.

**Reglas:**
- Solo el Administrador puede utilizar esta funcionalidad.
- Los resultados deben corresponder a los criterios ingresados.
- La búsqueda no modifica los datos de los usuarios.

---

## CU-11 — Utilizar chatbot de asistencia

**Actor principal:** Usuario autenticado (Estudiante, Profesor o Administrador).

**Objetivo:** permitir que los usuarios realicen consultas sobre el funcionamiento de la plataforma y obtengan información real del sistema mediante un chatbot basado en inteligencia artificial, respetando los permisos correspondientes a su rol.

**Precondiciones:**
- El usuario inició sesión en la plataforma.
- El usuario posee uno de los roles definidos en el sistema: Estudiante, Profesor o Administrador.
- El servicio del chatbot se ejecuta localmente en el entorno del sistema y se encuentra disponible para recibir consultas.
- Las fuentes de información necesarias se encuentran disponibles.

**Flujo principal:**
1. El usuario accede al chatbot desde la plataforma.
2. El sistema habilita la interfaz de conversación.
3. El usuario ingresa una consulta.
4. El sistema identifica al usuario autenticado y su rol.
5. El chatbot analiza la consulta para determinar qué información necesita para responder.
6. Si la consulta se relaciona con el funcionamiento de la plataforma, el chatbot utiliza principalmente la documentación correspondiente y puede recurrir a sus conocimientos generales cuando resulte útil.
7. Si la consulta requiere información real del sistema, el chatbot obtiene los datos necesarios de la base de datos mediante las operaciones autorizadas para el rol del usuario.
8. El chatbot utiliza el contexto de la conversación actual y, cuando corresponda, el historial de conversaciones anteriores del mismo usuario.
9. El chatbot genera una respuesta en español, clara y amable, cuya extensión se adapta a la consulta.
10. El sistema muestra la respuesta al usuario.
11. El usuario puede continuar la conversación realizando nuevas consultas.

**Flujo alternativo A1 — Usuario no autenticado:**
1. Una persona intenta acceder al chatbot sin haber iniciado sesión.
2. El sistema impide el acceso al chatbot.
3. El sistema solicita que la persona inicie sesión para utilizarlo.

**Flujo alternativo A2 — Consulta sobre información no disponible:**
1. El usuario realiza una consulta que requiere información que no se encuentra disponible o que no puede determinarse con suficiente certeza.
2. El chatbot informa que no dispone de información suficiente para responder con certeza.
3. Cuando resulte útil, proporciona información general relacionada, sin presentarla como un dato confirmado de la plataforma.
4. Cuando corresponda, recomienda consultar con un profesor o administrador.

**Flujo alternativo A3 — Consulta sobre información no autorizada:**
1. El usuario solicita información que excede los permisos correspondientes a su rol.
2. El sistema impide el acceso a dicha información.
3. El chatbot informa que no puede proporcionar los datos solicitados.

**Flujo alternativo A4 — Solicitud de modificación o ejecución de operaciones:**
1. El usuario solicita crear, modificar o eliminar información de la plataforma mediante el chatbot.
2. El chatbot informa que no puede ejecutar esa operación y, cuando corresponda, orienta al usuario hacia la funcionalidad correspondiente de la plataforma.

**Flujo alternativo A5 — Solicitud de corrección o calificación de tareas:**
1. El usuario solicita que el chatbot corrija una entrega o asigne una calificación.
2. El chatbot informa que esas operaciones no forman parte de sus funciones y que corresponden al profesor.

**Flujo alternativo A6 — Consulta ajena a la función del chatbot:**
1. El usuario realiza una consulta que no está relacionada con el funcionamiento de la plataforma educativa.
2. El chatbot explica brevemente que su función es ayudar a utilizar la plataforma y consultar información del sistema.
3. El chatbot redirige al usuario hacia ese propósito sin responder la consulta ajena a su función.

**Flujo alternativo A7 — Error al consultar información o generar una respuesta:**
1. Se produce un error que impide consultar la base de datos o generar una respuesta.
2. El chatbot informa que no pudo completar la consulta.
3. Cuando corresponda, indica que el usuario puede intentarlo nuevamente.

**Flujo alternativo A8 — Consulta relacionada con una conversación anterior:**
1. El usuario realiza una consulta que hace referencia a una conversación previa.
2. El chatbot recupera el historial disponible correspondiente a ese usuario.
3. El chatbot utiliza el contexto recuperado para interpretar y responder la consulta.
4. Si no dispone del contexto necesario, informa la limitación y solicita la información que falte cuando sea necesario.

**Postcondiciones:**
- El usuario recibe una respuesta o una explicación de por qué no puede responderse su consulta.
- La información proporcionada respeta los permisos de acceso correspondientes al rol del usuario.
- Las consultas de información se realizan sin modificar los datos de la plataforma.
- El historial de conversaciones se conserva asociado a la cuenta del usuario para permitir su utilización como contexto en futuras conversaciones.

**Reglas:**
- Solo los usuarios autenticados con los roles Estudiante, Profesor o Administrador pueden utilizar esta funcionalidad.
- El chatbot se ejecuta localmente: el modelo de lenguaje y el procesamiento de las consultas ocurren en el entorno del sistema, sin depender de servicios externos en la nube.
- El chatbot debe respetar los permisos de acceso existentes en la plataforma para cada rol.
- El chatbot no debe revelar información a usuarios que no estén autorizados a consultarla.
- Los datos concretos sobre cursos, inscripciones, tareas, entregas y calificaciones deben obtenerse de las fuentes autorizadas del sistema. El chatbot no debe inventar ni presentar como confirmados datos que no pudo verificar.
- La documentación de la plataforma constituye la fuente principal para explicar su funcionamiento. Los conocimientos generales del modelo pueden utilizarse como complemento, pero no deben utilizarse para inventar funcionalidades o reglas de la aplicación.
- El chatbot no puede crear, modificar ni eliminar información de la plataforma, ni ejecutar operaciones en nombre del usuario.
- El chatbot no puede corregir entregas ni asignar calificaciones. Estas operaciones corresponden al profesor.
- Cuando no disponga de información suficiente, el chatbot debe reconocer sus limitaciones, evitar especular y recomendar consultar con un profesor o administrador cuando corresponda.
- El chatbot debe limitar sus respuestas a las funciones definidas para la plataforma educativa. Ante consultas ajenas a ellas, debe explicar brevemente su alcance y redirigir al usuario.
- El chatbot debe responder en español, utilizando un tono claro y amable y adaptando la extensión de sus respuestas a cada consulta.
- El historial de conversaciones debe mantenerse asociado al usuario correspondiente y no puede ser accesible por otros usuarios sin autorización.
- Al utilizar conversaciones anteriores como contexto, el chatbot debe priorizar los datos actuales y verificados del sistema cuando la consulta requiera información actualizada.
- Las validaciones de identidad y permisos deben realizarse en el backend y no depender únicamente de las instrucciones proporcionadas al modelo de inteligencia artificial.
