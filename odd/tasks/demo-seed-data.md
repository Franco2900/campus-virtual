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

## Criterios de aceptación

- `alembic_version` = `0006` y la tabla `submission` existe.
- La base de desarrollo queda con, al menos: ≥ 8 cursos, ≥ 6 docentes, ≥ 16 estudiantes, ≥ 25 inscripciones activas, ≥ 20 tareas y ≥ 40 entregas.
- Correr `scripts/seed_demo.py` dos veces seguidas no duplica registros.
- No hay entregas cuyo estudiante no esté inscripto en el curso de la tarea (`activo`), ni entregas duplicadas por (tarea, estudiante).
- `ruff check backend` sigue OK (el script no introduce hallazgos nuevos en `scripts/`, fuera del target documentado).

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

### Pendiente
- Commit de la unidad (a la espera de confirmación del usuario por la restricción "no subir nada a git").
