# Feature: demo-seed-data — Actualizar la base y ampliar los datos de prueba

## Objetivo

Dejar la base de desarrollo del Campus Virtual con el esquema al día (migración `0006`, tabla `submission`) y con un volumen **mucho mayor** de datos de prueba coherentes: cursos, docentes, estudiantes, asignaciones Profesor↔curso, inscripciones, tareas y entregas.

## Problema / por qué

- La base de desarrollo (`backend/instance/campus.db`) está en `alembic 0005`: falta la tabla `submission` de CU-07.
- Los datos de prueba son escasos y desactualizados: 4 cursos, 2 docentes, 6 estudiantes, 10 inscripciones, **0 tareas y 0 entregas**. Sin tareas/entregas no se puede probar a mano CU-07 (ni preparar CU-08/CU-09).
- Pedido explícito del usuario: actualizar la base y agregar muchos más datos de prueba. No se sube nada a git.

## Alcance

- **Sí:** aplicar migraciones pendientes a la base de desarrollo; ampliar `scripts/seed_demo.py` (idempotente) con más cursos, docentes, estudiantes, asignaciones, inscripciones, tareas y entregas; ejecutar los seeds; verificar conteos y coherencia.
- **No:** tocar la base real de otros entornos, borrar datos existentes (operación destructiva no autorizada), cambiar `seed_admin.py` ni el modelo/migraciones, subir a git.

## Restricciones y supuestos

- Idempotencia obligatoria: cada registro se busca por clave natural antes de insertar (email; par curso+docente; par curso+estudiante; par curso+título de tarea; par tarea+estudiante).
- Reglas de negocio de datos: inscripción solo entre estudiante activo y curso activo; tarea pertenece a un curso; entrega única por (tarea, estudiante); entrega solo de un estudiante inscripto en el curso de la tarea.
- Coherencia temporal: las tareas usan `due_date` en UTC; se mezclan futuras y vencidas, y tareas activas/inactivas.
- Portabilidad: rutas relativas, sin rutas absolutas en el código de la app; comandos documentados para Windows/Linux/macOS.
- Se preservan los datos ya existentes (la base tiene `admin@example.com` y los cursos PROG1/MAT1/HIST1/FIS1): los seeds son aditivos.

## Ruta de implementación

- **Ruta:** directa inline de 1 escritor. **Motivo de la desviación:** el subagente `task` (delegación) falla por tier del proveedor (mismo error que `reviewer`, ver `errores.md`), así que no es posible delegar; se ejecuta inline con lecturas acotadas de los modelos.
- **TDD:** desactivado (`openspec/config.yaml` → `strict_tdd: false`, sin runner exigido) → verificación funcional, no RED/GREEN.
- **Estrategia de entrega:** `ask-on-risk`. Pronóstico de líneas cambiadas: ~250-350 (dominadas por listas de datos) → por debajo de 400, sin necesidad de dividir.

## Checklist

- [x] T1. Aplicar la migración `0006` a la base de desarrollo y verificar que exista la tabla `submission` (`alembic_version` = `0006`).
- [x] T2. Ampliar `scripts/seed_demo.py`: cursos extra, más docentes y estudiantes, asignaciones, inscripciones, **tareas** y **entregas** (todo idempotente por clave natural).
- [x] T3. Ejecutar los seeds contra la base de desarrollo y verificar los conteos por tabla.
- [x] T4. Verificación funcional: que un Estudiante vea las tareas disponibles con su entrega propia y que el `UNIQUE(task_id, student_id)` no se viole.
- [x] T5. Ampliar `TASK_TEMPLATES` a 10 plantillas por curso (8 activas / 2 inactivas) y re-ejecutar el seed sobre la base de desarrollo.
- [x] T6. Corregir una porción determinista de las entregas en el seed (notas que cubren aprobados y desaprobados) y dejar ~20% sin corregir para practicar CU-08.
- [x] T7. Reemplazar el contenido corto de las entregas del seed por textos largos multipárrafo y ampliar los enlaces a 2-3 por entrega; propagar el cambio a la base de desarrollo existente.

## Criterios de aceptación

- `alembic_version` = `0006` y la tabla `submission` existe.
- La base de desarrollo queda con, al menos: ≥ 8 cursos, ≥ 6 docentes, ≥ 16 estudiantes, ≥ 25 inscripciones activas, ≥ 20 tareas y ≥ 40 entregas.
- Correr `scripts/seed_demo.py` dos veces seguidas no duplica registros.
- No hay entregas cuyo estudiante no esté inscripto en el curso de la tarea (`activo`), ni entregas duplicadas por (tarea, estudiante).
- `ruff check backend` sigue OK (el script no introduce hallazgos nuevos en `scripts/`, fuera del target documentado).
- (T5) Cada curso activo queda con 10 tareas: 8 activas (6 a futuro y 2 vencidas) y 2 inactivas.
- (T6) La base sembrada queda con entregas corregidas que cubren todo el rango de notas (incluido el 6, borde de aprobación) y con alrededor del 20% sin corregir; ninguna corrección hecha a mano se sobrescribe.
- (T7) Las entregas sembradas tienen contenido largo multipárrafo (≥ 400 caracteres) y entre 1 y 3 enlaces; el texto corto original se conserva solo en el seed como fallback histórico, no se inserta.

## Verificación

- `.\\.venv\\Scripts\\python.exe scripts\\seed_demo.py` (aplica migraciones + siembra).
- Chequeo de conteos y de coherencia con SQLite directo.
- Re-ejecución para confirmar idempotencia.

## Progreso

### T1 — Migración aplicada (completado)
- `flask --app app db upgrade` desde `backend/` → `Running upgrade 0005 -> 0006, add submission`.
- Verificado: `alembic_version = 0006`, tablas `[alembic_version, course, course_teacher, enrollment, submission, task, user]`.

### T2 — Seeds ampliados (completado)
- `scripts/seed_demo.py` reescrito: cursos extra `DEMO_EXTRA_COURSES` (ALG1, BD1, REDES1, QUIM1, PROG2, ING1), docentes `DEMO_TEACHERS` (6), estudiantes `DEMO_STUDENTS` (18, dos inactivos: alumno6 y alumno18), asignaciones `DEMO_ASSIGNMENTS` (14), inscripciones base + `build_demo_enrollments()` (generadas), `TASK_TEMPLATES` + `build_demo_tasks()` (4 tareas por curso activo: 2 a futuro, 1 vencida, 1 inactiva), `_seed_submissions()` (pares deterministas tarea+estudiante inscripto activo; omite tareas inactivas).
- Helpers de idempotencia nuevos: `_get_task(course_id, title)`, `_get_submission(task_id, student_id)`.
- `main()` reporta conteos de las 7 categorías.

### T3 — Ejecución y conteos (completado)
- Primera corrida: cursos +6, docentes +4, estudiantes +12, asignaciones +10, inscripciones +46, tareas +36, entregas +108.
- Totales en `backend/instance/campus.db`: user 25 (1 admin, 6 docentes, 18 estudiantes: 16 activos), course 10 (9 activos), course_teacher 14, enrollment 56 (54 activos), task 36 (27 activas, 9 vencidas, 9 cursos con tareas), submission 108.
- Coherencia: 108 pares (tarea, estudiante) distintos; 0 entregas de estudiantes no inscriptos activos; 0 entregas sobre tareas inactivas; 0 `content` vacío; 0 `links` inválidos; 53 entregas con links.
- Idempotencia: segunda corrida → todas las categorías en 0; conteos sin cambios.

### T4 — Verificación funcional (completado)
- `alumno1@campus.edu` (4 inscripciones activas): ve 2 tareas disponibles por curso (ocultas: 1 vencida + 1 inactiva); 6 de 8 tareas disponibles tienen su entrega adjunta; las entregas apuntan a la tarea correcta y al estudiante correcto.
- Docente (`docente1@campus.edu`, PROG1/MAT1/PROG2): ve las 4 tareas de cada curso (incl. inactivas) y ninguna entrega adjunta.
- `pytest tests/test_migrations.py -q` → 1 passed.

### T5 — Más tareas por curso (completado)
- Pedido del usuario: «agrega más datos de prueba de las tareas, que por el momento hay muy pocas».
- `TASK_TEMPLATES` pasó de 4 a 10 plantillas: `Trabajo Práctico 1..4`, `Cuestionario de autoevaluación`, `Ejercicios de repaso`, `Recuperatorio del primer parcial`, `Trabajo final integrador` (8 activas: 6 a futuro y 2 vencidas) más `Parcial práctico` y `Actividad complementaria` (2 inactivas). Se conservaron los 4 títulos originales para no romper la clave natural `(course_id, title)`.
- Corrida del seed sobre la base de desarrollo: **+54 tareas** (6 plantillas nuevas × 9 cursos activos) y **+176 entregas**.
- Conteos antes → después: tareas **36 → 90** (activas 27 → 72; inactivas 9 → 18); entregas **108 → 284**; por curso **4 → 10 tareas** en los 9 cursos.
- Idempotencia re-verificada: segunda corrida inmediata → todas las categorías en 0, conteos sin cambios.
- Verificación por endpoints reales (test client de Flask contra la base de desarrollo, solo GETs): `docente1@campus.edu` → `GET /api/courses/1/tasks` = 10 (8 activas / 2 inactivas); `GET /api/courses/1/grades` = 8 columnas de tarea, 6 estudiantes y `approved` presente y correcto (Ana López, promedio 8.0 → Aprobado).
- **Efecto lateral (reportado al usuario):** la nueva tarea activa vencida (`Recuperatorio del primer parcial`, −10 días) baja los promedios, porque una tarea vencida **sin** entrega cuenta como 1. Ej.: Bruno Díaz 6.5 → 4.6667. Combinado con que ninguna entrega nacía corregida, la mayoría de los estudiantes quedaba "Desaprobado" en la demo (resuelto por T6).

### T6 — Entregas corregidas en el seed (completado)
- Pedido del usuario: «que el seed cargue también entregas ya corregidas» y dejar los servicios levantados para probar a mano.
- Nueva función `_seed_grades()`: recorre **solo** las entregas con `grade IS NULL` (por lo tanto preserva cualquier corrección hecha a mano), corrige ~80% (saltea `(task_id + student_id) % 5 == 4`) y asigna la nota del ciclo `GRADE_CYCLE` más el texto de `GRADE_FEEDBACKS`.
- El ~20% que queda sin corregir es deliberado: es el material para practicar CU-08 en la UI.
- `graded_at` se ancla al vencimiento de la tarea + 2 días, acotado a "ahora"; el helper `_as_utc()` normaliza los `DateTime` que SQLite devuelve sin zona, evitando comparar `naive` con `aware`.
- Detalle detectado y corregido en la misma tarea: con el ciclo original (largo 10) la nota 6 caía **siempre** en la posición salteada, porque `bucket % 10 == 4` implica `bucket % 5 == 4`; la última retroalimentación tampoco se usaba nunca. Se pasaron los ciclos a longitudes coprimas con 5 (8 notas y 6 textos).
- Verificación en base temporal limpia (`CAMPUS_DB_PATH` + `seed_admin.py` + `seed_demo.py`): 289 entregas, 241 corregidas / 48 pendientes (83%/17%), 151 aprobadas / 90 desaprobadas, distribución completa **3, 4, 5, 6, 7, 8, 9, 10**, 0 corregidas sin `graded_at`, 0 con `graded_at` futuro y las 5 retroalimentaciones no vacías usadas.
- Idempotencia: segunda corrida sobre la base temporal y sobre la de desarrollo → 0 creados / 0 corregidos.
- Verificación por API real (test client, solo GETs) sobre la base de desarrollo: `docente1` en PROG1 → 8 columnas de tarea, promedio del curso 6.07, matriz con 3 aprobados (6.5 / 6.4 / 6.2) y 3 desaprobados (5.83 / 5.8 / 5.67); `alumno1` → promedio 6.5, con notas 8, 3, 7 y 8 y las tareas sin corregir en "—".
- Servicios levantados para prueba manual con `scripts/verify.py --serve --db backend/instance/campus.db` (backend 5000 + Vite 5173, desligados); verificado: frontend 200, proxy `/api` → 401 sin sesión, backend directo 401.

### T7 — Entregables largos y con enlaces (completado)
- Pedido del usuario: «que los entregables de los alumnos sean más largos y con enlaces»; los textos cortos originales (`"Entrego el trabajo completo con las consignas resueltas."`, etc.) no daban sensación de trabajo real en la UI de corrección.
- `scripts/seed_demo.py`: `SUBMISSION_CONTENTS` reemplazado por 5 textos multipárrafo (con encabezados y secciones: introducción / marco teórico / desarrollo / conclusiones; ~400-1100 caracteres); `SUBMISSION_LINKS` ampliado a 5 conjuntos de 2-3 enlaces (`example.com`, `docs.google.com`, `github.com/alumno-demo`, `drive.google.com`, `capturas-evidencia`).
- Propagación a la base existente: el seed es insert-only, así que la re-ejecución reportó «Entregas creadas: 0» y las 284 entregas de desarrollo seguían con el texto corto. Se aplicó una migración de contenido acotada (script temporal fuera del repo) que **solo** reescribe las entregas cuyo `content` coincide con alguno de los 5 textos cortos originales (o mide < 120 caracteres), preservando cualquier entrega editada a mano. Actualizadas: 284.
- Verificación en base temporal limpia (`seed_check_long.db`): contenido hasta 1111 caracteres, enlaces por entrega presentes, 241 corregidas / 48 pendientes (sin cambios respecto de T6).
- Verificación sobre la base de desarrollo: `alumno1` tarea 1 → `content` 1111 caracteres y 2 enlaces; `GET /api/courses/1/grades` sigue devolviendo promedio 6.5 y notas 8/3/7/8.
- `pytest -q` (suite completo): 222 passed. `py_compile` del seed OK. `ruff check backend`: sin cambios (el script está fuera del target de lint).
- Servicios re-levantados con `scripts/verify.py --serve --db backend/instance/campus.db` para la prueba manual; PIDs en `scripts/.verify-pids`.

### Pendiente
- (cerrado) Unidad commiteada y publicada: commit `4cd67bd feat(seed): expand demo data with courses, tasks and submissions`; merge fast-forward de CU-07 a `main` y push a `origin/main` (`1139470..4cd67bd`).
- Nota: por decisión del usuario, CU-07 y los seeds se publicaron juntos en `main` (no se abrió PR); la rama local `feat/cu-07-task-submission` quedó mergeada (fast-forward) y puede borrarse.
- (abierto) Commit pendiente: la ampliación de `TASK_TEMPLATES` se batchea con el ajuste de UI del estado de aprobación en el Profesor (decisión del usuario).
- (cerrado) Mejora del seed que faltaba: ninguna entrega nacía corregida (`grade=None`). Resuelto por T6 (`_seed_grades()`), con distribución determinista que cubre aprobados y desaprobados.
- (nota) La base de desarrollo se corrigió con el ciclo *anterior* a T6, así que hoy no tiene ninguna nota exacta 6; el script ya es correcto y una base sembrada desde cero sí la incluye. Recargar las notas de la base de desarrollo sería una operación destructiva: queda a decisión del usuario.
- (abierto) T7 dejó la base de desarrollo con el contenido largo aplicado mediante un script temporal; si más adelante se quiere que el seed actualice contenido por sí solo, habría que agregar una función `_seed_submission_content()` idempotente al script (hoy no existe).
