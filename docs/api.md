# API — Campus Virtual

Contrato de la API REST del Campus Virtual: fuente de verdad de rutas, roles y códigos de estado. Los cuerpos de request se indican inline en la columna Propósito cuando aplica.
No inventar endpoints. Cubre CU-01..CU-12, implementados, verificados y archivados; los códigos de cada fila listan el conjunto completo que el handler y sus guards pueden devolver.

## Endpoints

| Método | Ruta | CU | Propósito | Auth |
|--------|------|----|-----------|------|
| POST | `/api/auth/register` | CU-01 | Registrar una cuenta (rol Estudiante) (201/400/409) | Público |
| POST | `/api/auth/login` | CU-02 | Iniciar sesión (emite cookie de sesión) (200/400/401) | Público |
| GET | `/api/auth/me` | CU-02 | Obtener el usuario autenticado (200/401) | Sesión |
| POST | `/api/auth/logout` | CU-02 | Cerrar sesión (idempotente; sin sesión responde 200) | Sesión |
| GET | `/api/courses` | CU-03 | Listar cursos (incluye inactivos) (200/401/403) | Sesión + Administrador |
| POST | `/api/courses` | CU-03 | Crear un curso (201/400/401/403/409) | Sesión + Administrador |
| GET | `/api/courses/<id>` | CU-03 | Obtener un curso (200/401/403/404) | Sesión + Administrador |
| PUT | `/api/courses/<id>` | CU-03 | Editar un curso (200/400/401/403/404/409) | Sesión + Administrador |
| PATCH | `/api/courses/<id>` | CU-03 | Activar/desactivar un curso — body `{"active": <bool>}` (200/400/401/403/404) | Sesión + Administrador |
| GET | `/api/users` | CU-04/CU-10 | Listar usuarios (incluye inactivos); filtros opcionales `q` (texto libre), `role` y `active` (`true`/`false`), combinados con AND (200/400/401/403; 400 con criterio inválido) | Sesión + Administrador |
| GET | `/api/users/<id>` | CU-04 | Obtener un usuario (200/401/403/404) | Sesión + Administrador |
| PUT | `/api/users/<id>` | CU-04 | Editar datos y rol (200/400/401/403/404/409) | Sesión + Administrador |
| PATCH | `/api/users/<id>` | CU-04 | Activar/desactivar — body `{"active": <bool>}` (200/400/401/403/404) | Sesión + Administrador |
| POST | `/api/users/<id>/password` | CU-04 | Resetear contraseña — body `{"password": "..."}` (200/400/401/403/404) | Sesión + Administrador |
| GET | `/api/courses/<id>/teachers` | CU-04 | Listar profesores del curso (200/401/403/404) | Sesión + Administrador |
| POST | `/api/courses/<id>/teachers` | CU-04 | Asignar profesor — body `{"teacher_id": <id>}` (201/400/401/403/404/409) | Sesión + Administrador |
| DELETE | `/api/courses/<id>/teachers/<teacher_id>` | CU-04 | Quitar profesor del curso (200/401/403/404) | Sesión + Administrador |
| GET | `/api/courses/mine` | CU-05 | Listar los cursos del usuario (Profesor: asignados; Estudiante: inscritos; Admin: todos) (200/401) | Sesión + Administrador/Profesor/Estudiante |
| GET | `/api/courses/<id>/students` | CU-05 | Listar estudiantes activos con su inscripción (200/401/403/404) | Sesión + Administrador/Profesor |
| POST | `/api/courses/<id>/students` | CU-05 | Inscribir estudiante — body `{"student_id": <id>}` (201/400/401/403/404/409) | Sesión + Administrador/Profesor |
| PATCH | `/api/courses/<id>/students/<student_id>` | CU-05 | Activar/desactivar inscripción — body `{"active": <bool>}` (200/400/401/403/404/409) | Sesión + Administrador/Profesor |
| DELETE | `/api/courses/<id>/students/<student_id>` | CU-05 | Eliminar inscripción (200/401/403/404) | Sesión + Administrador/Profesor |
| GET | `/api/courses/<id>/tasks` | CU-06/07 | Listar tareas del curso (Profesor: activas e inactivas; Estudiante: disponibles + entrega propia) (200/401/403/404) | Sesión + Profesor/Estudiante |
| POST | `/api/courses/<id>/tasks` | CU-06 | Crear una tarea (201/400/401/403/404/409) | Sesión + Profesor |
| GET | `/api/courses/<id>/tasks/<task_id>` | CU-06 | Obtener una tarea (200/401/403/404) | Sesión + Profesor |
| PUT | `/api/courses/<id>/tasks/<task_id>` | CU-06 | Editar una tarea, incl. fecha límite (200/400/401/403/404/409) | Sesión + Profesor |
| PATCH | `/api/courses/<id>/tasks/<task_id>` | CU-06 | Activar/desactivar tarea — body `{"active": <bool>}` (200/400/401/403/404) | Sesión + Profesor |
| POST | `/api/courses/<id>/tasks/<task_id>/submission` | CU-07 | Entregar una tarea — body `{"content", "links"}` (201/400/401/403/404/409) | Sesión + Estudiante |
| PUT | `/api/courses/<id>/tasks/<task_id>/submission` | CU-07 | Modificar la entrega propia (200/400/401/403/404/409) | Sesión + Estudiante |
| DELETE | `/api/courses/<id>/tasks/<task_id>/submission` | CU-07 | Eliminar la entrega propia (200/401/403/404/409) | Sesión + Estudiante |
| GET | `/api/courses/<id>/tasks/<task_id>/submissions` | CU-08 | Listar las entregas de la tarea con datos del estudiante y estado de corrección (200/401/403/404) | Sesión + Profesor |
| PUT | `/api/courses/<id>/tasks/<task_id>/submissions/<student_id>/grade` | CU-08 | Corregir o modificar una entrega — body `{"grade": 1..10, "feedback"?: str}` (200/400/401/403/404) | Sesión + Profesor |
| GET | `/api/courses/<id>/grades` | CU-09 | Consultar calificaciones del curso según el rol (Estudiante: sus notas, retroalimentación y promedio; Profesor: matriz estudiante × tarea y promedio del curso) (200/401/403/404) | Sesión + Profesor/Estudiante |
| POST | `/api/chat/messages` | CU-11 | Enviar una consulta al chatbot y obtener la respuesta del asistente — body `{"content": "..."}` (201/400/401/502) | Sesión + Estudiante/Profesor/Administrador |
| GET | `/api/chat/messages` | CU-11 | Obtener el historial de la conversación del usuario autenticado (200/401) | Sesión + Estudiante/Profesor/Administrador |
| DELETE | `/api/chat/messages` | CU-11 | Eliminar el historial de conversaciones del usuario (200 idempotente; 401 sin sesión) | Sesión + Estudiante/Profesor/Administrador |
| GET | `/api/knowledge/sources` | CU-12 | Listar fuentes de conocimiento con estado y errores de indexado (200/401/403) | Sesión + Administrador |
| POST | `/api/knowledge/sources` | CU-12 | Cargar e indexar una fuente (multipart: `file` `.md`/`.txt` ≤ 1 MB, `name`, `description?`, `source_type`, `target_roles?`) (201/400/401/403) | Sesión + Administrador |
| DELETE | `/api/knowledge/sources/<id>` | CU-12 | Eliminar una fuente: índice vectorial → archivo → fila (200/401/403/404/500) | Sesión + Administrador |

> Contrato vigente de los 39 endpoints (CU-01..CU-12). No inventar endpoints.

