"""Provisiona datos de demostración ampliados del Campus Virtual.

Crea cursos extra, Profesores, Estudiantes (uno inactivo), asignaciones
Profesor↔curso, inscripciones (activas e inactivas), tareas (activas/inactivas,
con plazos futuros y vencidos), entregas de tareas y la corrección de una porción
determinista de esas entregas, sobre los cursos demo ya sembrados por
`scripts/seed_admin.py`. Es idempotente: cada registro se busca por su clave natural
(email, par curso+profesor, par curso+estudiante, par curso+título de tarea, par
tarea+estudiante) antes de insertarse, y solo se corrigen entregas sin calificar.

Uso (desde la raíz del proyecto, con el Administrador y los cursos demo ya creados):
    Windows:     .\\.venv\\Scripts\\python.exe scripts\\seed_demo.py
    Linux/macOS: .venv/bin/python scripts/seed_demo.py

Contraseñas de demo (se pueden sobreescribir por entorno):
    CAMPUS_DEMO_TEACHER_PASSWORD (default "Docente123")
    CAMPUS_DEMO_STUDENT_PASSWORD (default "Alumno123")
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from flask_migrate import upgrade as apply_migrations
from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from models.base import db  # noqa: E402
from models.course import Course  # noqa: E402
from models.course_teacher import CourseTeacher  # noqa: E402
from models.enrollment import Enrollment  # noqa: E402
from models.submission import Submission  # noqa: E402
from models.task import Task  # noqa: E402
from models.user import User, UserRole  # noqa: E402

TEACHER_PASSWORD_ENV = "CAMPUS_DEMO_TEACHER_PASSWORD"
STUDENT_PASSWORD_ENV = "CAMPUS_DEMO_STUDENT_PASSWORD"
DEFAULT_TEACHER_PASSWORD = "Docente123"
DEFAULT_STUDENT_PASSWORD = "Alumno123"

# Cursos adicionales de demostración (los cuatro base los crea seed_admin.py).
DEMO_EXTRA_COURSES = [
    {
        "name": "Álgebra",
        "code": "ALG1",
        "description": "Estructuras algebraicas y matrices.",
        "active": True,
    },
    {
        "name": "Base de Datos",
        "code": "BD1",
        "description": "Modelado relacional, SQL y transacciones.",
        "active": True,
    },
    {
        "name": "Redes",
        "code": "REDES1",
        "description": "Modelo OSI/TCP-IP y protocolos de red.",
        "active": True,
    },
    {
        "name": "Química",
        "code": "QUIM1",
        "description": "Química general y estequiometría.",
        "active": True,
    },
    {
        "name": "Programación II",
        "code": "PROG2",
        "description": "Estructuras de datos y programación orientada a objetos.",
        "active": True,
    },
    {
        "name": "Inglés",
        "code": "ING1",
        "description": "Inglés técnico para informática.",
        "active": True,
    },
]

DEMO_TEACHERS = [
    {"first_name": "Laura", "last_name": "Gómez", "email": "docente1@campus.edu"},
    {"first_name": "Martín", "last_name": "Pérez", "email": "docente2@campus.edu"},
    {"first_name": "Sofía", "last_name": "Río", "email": "docente3@campus.edu"},
    {"first_name": "Andrés", "last_name": "Silva", "email": "docente4@campus.edu"},
    {"first_name": "Valentina", "last_name": "Novoa", "email": "docente5@campus.edu"},
    {"first_name": "Ignacio", "last_name": "Herrera", "email": "docente6@campus.edu"},
]

DEMO_STUDENTS = [
    {
        "first_name": "Ana",
        "last_name": "López",
        "email": "alumno1@campus.edu",
        "active": True,
    },
    {
        "first_name": "Bruno",
        "last_name": "Díaz",
        "email": "alumno2@campus.edu",
        "active": True,
    },
    {
        "first_name": "Carla",
        "last_name": "Fernández",
        "email": "alumno3@campus.edu",
        "active": True,
    },
    {
        "first_name": "Diego",
        "last_name": "Sosa",
        "email": "alumno4@campus.edu",
        "active": True,
    },
    {
        "first_name": "Elena",
        "last_name": "Ruiz",
        "email": "alumno5@campus.edu",
        "active": True,
    },
    {
        "first_name": "Fabián",
        "last_name": "Molina",
        "email": "alumno6@campus.edu",
        "active": False,
    },
    {
        "first_name": "Gabriela",
        "last_name": "Torres",
        "email": "alumno7@campus.edu",
        "active": True,
    },
    {
        "first_name": "Hernán",
        "last_name": "Aguirre",
        "email": "alumno8@campus.edu",
        "active": True,
    },
    {
        "first_name": "Inés",
        "last_name": "Benítez",
        "email": "alumno9@campus.edu",
        "active": True,
    },
    {
        "first_name": "Joaquín",
        "last_name": "Castro",
        "email": "alumno10@campus.edu",
        "active": True,
    },
    {
        "first_name": "Karen",
        "last_name": "Domínguez",
        "email": "alumno11@campus.edu",
        "active": True,
    },
    {
        "first_name": "Lucas",
        "last_name": "Escobar",
        "email": "alumno12@campus.edu",
        "active": True,
    },
    {
        "first_name": "Mariana",
        "last_name": "Figueroa",
        "email": "alumno13@campus.edu",
        "active": True,
    },
    {
        "first_name": "Nicolás",
        "last_name": "Giménez",
        "email": "alumno14@campus.edu",
        "active": True,
    },
    {
        "first_name": "Olivia",
        "last_name": "Herrera",
        "email": "alumno15@campus.edu",
        "active": True,
    },
    {
        "first_name": "Pablo",
        "last_name": "Ibarra",
        "email": "alumno16@campus.edu",
        "active": True,
    },
    {
        "first_name": "Rocío",
        "last_name": "Juárez",
        "email": "alumno17@campus.edu",
        "active": True,
    },
    {
        "first_name": "Santiago",
        "last_name": "Klein",
        "email": "alumno18@campus.edu",
        "active": False,
    },
]

# (teacher_email, course_code)
DEMO_ASSIGNMENTS = [
    ("docente1@campus.edu", "PROG1"),
    ("docente1@campus.edu", "MAT1"),
    ("docente1@campus.edu", "PROG2"),
    ("docente2@campus.edu", "FIS1"),
    ("docente2@campus.edu", "PROG1"),
    ("docente2@campus.edu", "BD1"),
    ("docente3@campus.edu", "ALG1"),
    ("docente3@campus.edu", "MAT1"),
    ("docente4@campus.edu", "BD1"),
    ("docente4@campus.edu", "PROG2"),
    ("docente5@campus.edu", "REDES1"),
    ("docente5@campus.edu", "ING1"),
    ("docente6@campus.edu", "QUIM1"),
    ("docente6@campus.edu", "FIS1"),
]

# (student_email, course_code, active) — solo cursos y cuentas activos
DEMO_ENROLLMENTS_BASE = [
    ("alumno1@campus.edu", "PROG1", True),
    ("alumno1@campus.edu", "MAT1", True),
    ("alumno2@campus.edu", "PROG1", True),
    ("alumno2@campus.edu", "FIS1", True),
    ("alumno3@campus.edu", "PROG1", True),
    ("alumno3@campus.edu", "MAT1", True),
    ("alumno4@campus.edu", "FIS1", True),
    ("alumno5@campus.edu", "MAT1", True),
    ("alumno5@campus.edu", "PROG1", False),
    ("alumno4@campus.edu", "MAT1", False),
]

# Cursos activos usados para generar inscripciones, tareas y entregas.
ACTIVE_COURSE_CODES = [
    "PROG1",
    "MAT1",
    "FIS1",
    "ALG1",
    "BD1",
    "REDES1",
    "QUIM1",
    "PROG2",
    "ING1",
]

# Plantillas de tareas por curso: (title, description, days_from_now, active).
# Los plazos negativos quedan vencidos; dos tareas por curso quedan inactivas.
TASK_TEMPLATES = [
    ("Trabajo Práctico 1", "Resolución de ejercicios de la unidad 1.", 7, True),
    ("Trabajo Práctico 2", "Resolución de ejercicios de la unidad 2.", 14, True),
    ("Trabajo Práctico 3", "Resolución de ejercicios de la unidad 3.", 21, True),
    ("Trabajo Práctico 4", "Resolución de ejercicios de la unidad 4.", 28, True),
    ("Cuestionario de autoevaluación", "Repaso de los temas del curso.", 10, True),
    ("Ejercicios de repaso", "Consolidación de los temas vistos en clase.", -3, True),
    (
        "Recuperatorio del primer parcial",
        "Instancia de recuperación para quienes no aprobaron.",
        -10,
        True,
    ),
    ("Trabajo final integrador", "Integra los contenidos vistos en el curso.", 42, True),
    ("Parcial práctico", "Evaluación integradora (se publica más adelante).", 21, False),
    ("Actividad complementaria", "Ejercicios adicionales de profundización.", 30, False),
]

SUBMISSION_CONTENTS = [
    "\n\nTrabajo Práctico: Entrega completa\n\nEnunciado desarrollado.\n\n1. Desarrollo teórico\n\nPara la presente entrega se procedió a analizar los fundamentos del tema asignado, revisando las fuentes bibliográficas indicadas y contrastando los distintos enfoques mencionados en la cursada. Se tomó como base el material teórico provisto y se profundizó en los ejemplos prácticos discutidos en clase, a fin de dar respuesta a todas las consignas solicitadas.\n\n2. Resolución práctica\n\nSe desarrollaron todos los ejercicios propuestos, mostrando de manera ordenada los pasos seguidos y los cálculos intermedios. Para aquellos puntos que requerían justificación, se incluyeron las razones que sustentan la solución propuesta. Asimismo, se verificaron los resultados obtenidos para minimizar posibles errores.\n\n3. Análisis y conclusiones\n\nA partir del trabajo realizado, se arribaron a las conclusiones pertinentes. Se identificaron las principales dificultades y las estrategias adoptadas para superarlas. Finalmente, se evaluó la aplicabilidad de los conceptos abordados a situaciones concretas vinculadas a la asignatura.\n",
    "\n\nDesarrollo de la actividad\n\nSe entrega la resolución completa de la actividad solicitada. El trabajo se estructura como sigue:\n\nIntroducción: breve contextualización del problema y los objetivos que se persiguen con esta entrega.\n\nMarco teórico: síntesis de los conceptos fundamentales utilizados, con la referencia a los temas de la cursada.\n\nDesarrollo: resolución detallada de cada punto, incluyendo diagramas, fórmulas y argumentos cuando corresponde.\n\nResultados: presentación clara y organizada de los resultados obtenidos.\n\nConclusión: principales hallazgos y reflexiones finales sobre el ejercicio desarrollado.\n",
    "\n\nInforme de resolución\n\nA continuación se presenta el desarrollo completo de la actividad:\n\n1. Objetivos\n\nEl presente trabajo tiene como objetivo aplicar los contenidos vistos en clase para resolver las consignas propuestas, poniendo especial atención a la claridad en la justificación de cada respuesta.\n\n2. Marco conceptual\n\nSe revisaron los conceptos teóricos necesarios para encarar la actividad. Se tuvieron en cuenta las definiciones, propiedades y criterios de aplicación vistos en la unidad correspondiente.\n\n3. Desarrollo\n\nSe resolvieron todos los puntos, mostrando cálculos, razonamientos y ejemplos cuando resultaba pertinente. Se prestó especial cuidado a la legibilidad y a la correcta aplicación de las fórmulas empleadas.\n\n4. Discusión\n\nSe analizan los resultados obtenidos, señalando las coincidencias y diferencias con los ejemplos vistos en clase.\n\n5. Conclusiones\n\nSe arriba a las conclusiones correspondientes y se proponen breves ideas para complementar el análisis.\n",
    "\n\nEntrega de la actividad práctica\n\nLa presente entrega incluye el desarrollo completo de todos los ítems propuestos. Para cada punto se ha detallado el procedimiento seguido, permitiendo así seguir la lógica empleada en la obtención de cada respuesta.\n\nSe han incluido las etapas de análisis, diseño y resolución. Además, se consideraron posibles validaciones de las soluciones encontradas a fin de asegurar su coherencia con lo solicitado en la consigna.\n",
    "\n\nTrabajo completo\n\nSe presenta la resolución completa de la actividad asignada. El enfoque adoptado fue el de justificar cada paso, dejando constancia de los razonamientos, de los recursos utilizados y de las decisiones tomadas a lo largo del proceso de resolución.\n\nEl trabajo abarca el desarrollo de la totalidad de los puntos, la verificación de los resultados y la síntesis final con conclusiones.\n",
]

SUBMISSION_LINKS = [
    [
        "https://example.com/entregas/tp-desarrollo",
        "https://docs.google.com/document/d/demo-entrega",
    ],
    [
        "https://github.com/alumno-demo/resolucion",
        "https://example.com/repositorio-anexo",
    ],
    [
        "https://docs.google.com/spreadsheets/d/demo-calculos",
        "https://example.com/informe-final",
    ],
    [
        "https://github.com/alumno-demo/tp-entrega",
        "https://docs.google.com/presentation/d/demo-presentacion",
    ],
    [
        "https://drive.google.com/file/d/demo-documento",
        "https://example.com/capturas-evidencia",
        "https://github.com/alumno-demo/suplemento",
    ],
]

# Calificaciones de demostración: ciclo determinista que cubre aprobados (>= 6) y
# desaprobados, para que la demo de CU-09 muestre ambos estados. Las longitudes del
# ciclo de notas y del de retroalimentaciones son coprimas con el módulo de salteo de
# `_seed_grades` (% 5); si no lo fueran, esa nota o ese texto quedarían sin asignarse.
GRADE_CYCLE = [9, 7, 6, 4, 10, 5, 8, 3]

GRADE_FEEDBACKS = [
    "",
    "Muy buen trabajo: completo y bien justificado.",
    "Faltó desarrollar los últimos puntos.",
    "Correcto en general; revisá el análisis del punto 3.",
    "Buen desarrollo, cuidá la presentación.",
    "Repasá la consigna 2 para la próxima entrega.",
]


class SeedError(Exception):
    pass


def read_passwords(environ=None):
    environ = os.environ if environ is None else environ
    teacher = environ.get(TEACHER_PASSWORD_ENV) or DEFAULT_TEACHER_PASSWORD
    student = environ.get(STUDENT_PASSWORD_ENV) or DEFAULT_STUDENT_PASSWORD
    return teacher, student


def ensure_schema(app):
    """Aplica las migraciones pendientes para garantizar el esquema vigente."""
    with app.app_context():
        apply_migrations(directory=str(MIGRATIONS_DIR))


def build_demo_enrollments():
    """Combina inscripciones base + una selección generada por estudiante activo."""
    enrollments = list(DEMO_ENROLLMENTS_BASE)
    active_students = [spec["email"] for spec in DEMO_STUDENTS if spec.get("active", True)]
    total = len(ACTIVE_COURSE_CODES)
    for index, email in enumerate(active_students):
        for offset in (0, 2, 5):
            code = ACTIVE_COURSE_CODES[(index + offset) % total]
            enrollments.append((email, code, True))
    return enrollments


def build_demo_tasks():
    """Genera (course_code, title, description, due_date, active) por curso activo."""
    now = datetime.now(UTC)
    tasks = []
    for code in ACTIVE_COURSE_CODES:
        for title, description, days, active in TASK_TEMPLATES:
            due_date = now + timedelta(days=days)
            tasks.append((code, title, description, due_date, active))
    return tasks


def _get_user(email):
    return db.session.execute(
        db.select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()


def _get_course(code):
    return db.session.execute(
        db.select(Course).where(Course.code == code)
    ).scalar_one_or_none()


def _get_task(course_id, title):
    return db.session.execute(
        db.select(Task).where(Task.course_id == course_id, Task.title == title)
    ).scalar_one_or_none()


def _get_submission(task_id, student_id):
    return db.session.execute(
        db.select(Submission).where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
        )
    ).scalar_one_or_none()


def _seed_courses(specs):
    created = 0
    for spec in specs:
        if _get_course(spec["code"]) is not None:
            continue
        db.session.add(Course(**spec))
        created += 1
    db.session.commit()
    return created


def _seed_users(specs, role, password_hash):
    created = 0
    for spec in specs:
        email = spec["email"].strip().lower()
        if _get_user(email) is not None:
            continue
        db.session.add(
            User(
                first_name=spec["first_name"],
                last_name=spec["last_name"],
                email=email,
                password_hash=password_hash,
                role=role,
                active=spec.get("active", True),
            )
        )
        created += 1
    db.session.commit()
    return created


def _seed_assignments(specs):
    created = 0
    for teacher_email, course_code in specs:
        teacher = _get_user(teacher_email)
        course = _get_course(course_code)
        if teacher is None or course is None:
            raise SeedError(
                f"Falta el Profesor ({teacher_email}) o el curso ({course_code}); "
                "corré primero scripts/seed_admin.py."
            )
        existing = db.session.execute(
            db.select(CourseTeacher).where(
                CourseTeacher.course_id == course.id,
                CourseTeacher.teacher_id == teacher.id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.session.add(CourseTeacher(course_id=course.id, teacher_id=teacher.id))
        created += 1
    db.session.commit()
    return created


def _seed_enrollments(specs):
    created = 0
    for student_email, course_code, active in specs:
        student = _get_user(student_email)
        course = _get_course(course_code)
        if student is None or course is None:
            raise SeedError(
                f"Falta el Estudiante ({student_email}) o el curso ({course_code}); "
                "corré primero scripts/seed_admin.py."
            )
        if not student.active or not course.active:
            continue
        existing = db.session.execute(
            db.select(Enrollment).where(
                Enrollment.course_id == course.id,
                Enrollment.student_id == student.id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        db.session.add(
            Enrollment(course_id=course.id, student_id=student.id, active=active)
        )
        created += 1
    db.session.commit()
    return created


def _seed_tasks(specs):
    created = 0
    for course_code, title, description, due_date, active in specs:
        course = _get_course(course_code)
        if course is None:
            raise SeedError(
                f"Falta el curso ({course_code}); corré primero scripts/seed_admin.py."
            )
        if _get_task(course.id, title) is not None:
            continue
        db.session.add(
            Task(
                course_id=course.id,
                title=title,
                description=description,
                due_date=due_date,
                active=active,
            )
        )
        created += 1
    db.session.commit()
    return created


def _seed_submissions():
    """Crea entregas para una porción determinista de pares (tarea, estudiante)
    inscripto y activo. Omite tareas inactivas (no publicadas)."""
    created = 0
    tasks = (
        db.session.execute(db.select(Task).where(Task.active.is_(True)).order_by(Task.id))
        .scalars()
        .all()
    )
    for task in tasks:
        students = (
            db.session.execute(
                db.select(User)
                .join(Enrollment, Enrollment.student_id == User.id)
                .where(
                    Enrollment.course_id == task.course_id,
                    Enrollment.active.is_(True),
                    User.active.is_(True),
                )
                .order_by(User.id)
            )
            .scalars()
            .all()
        )
        for index, student in enumerate(students):
            if (task.id + index) % 3 == 2:
                continue
            if _get_submission(task.id, student.id) is not None:
                continue
            bucket = task.id + index
            links = SUBMISSION_LINKS[bucket % len(SUBMISSION_LINKS)] if bucket % 2 == 0 else []
            db.session.add(
                Submission(
                    task_id=task.id,
                    student_id=student.id,
                    content=SUBMISSION_CONTENTS[bucket % len(SUBMISSION_CONTENTS)],
                    links=links,
                )
            )
            created += 1
    db.session.commit()
    return created


def _as_utc(value):
    """Normaliza a UTC: SQLite devuelve los `DateTime` sin información de zona."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _seed_grades():
    """Corrige una porción determinista de las entregas sin calificar.

    Deja alrededor de un 20% sin corregir para poder practicar CU-08, y solo toca
    entregas con `grade` nulo, así que preserva las correcciones hechas a mano.
    """
    now = datetime.now(UTC)
    due_dates = {
        task.id: task.due_date for task in db.session.execute(db.select(Task)).scalars()
    }
    pending = (
        db.session.execute(
            db.select(Submission).where(Submission.grade.is_(None)).order_by(Submission.id)
        )
        .scalars()
        .all()
    )
    graded = 0
    for submission in pending:
        bucket = submission.task_id + submission.student_id
        if bucket % 5 == 4:
            continue
        due_date = due_dates.get(submission.task_id)
        graded_at = min(_as_utc(due_date) + timedelta(days=2), now) if due_date else now
        submission.grade = GRADE_CYCLE[bucket % len(GRADE_CYCLE)]
        submission.feedback = GRADE_FEEDBACKS[bucket % len(GRADE_FEEDBACKS)]
        submission.graded_at = graded_at
        graded += 1
    db.session.commit()
    return graded


def main():
    try:
        teacher_password, student_password = read_passwords()
    except SeedError as error:
        print(str(error), file=sys.stderr)
        return 1

    app = create_app()
    ensure_schema(app)

    with app.app_context():
        if _get_course("PROG1") is None:
            print(
                "No hay cursos demo; corré primero scripts/seed_admin.py.",
                file=sys.stderr,
            )
            return 1

        courses_created = _seed_courses(DEMO_EXTRA_COURSES)
        teachers_created = _seed_users(
            DEMO_TEACHERS, UserRole.TEACHER, generate_password_hash(teacher_password)
        )
        students_created = _seed_users(
            DEMO_STUDENTS, UserRole.STUDENT, generate_password_hash(student_password)
        )
        assignments_created = _seed_assignments(DEMO_ASSIGNMENTS)
        enrollments_created = _seed_enrollments(build_demo_enrollments())
        tasks_created = _seed_tasks(build_demo_tasks())
        submissions_created = _seed_submissions()
        grades_created = _seed_grades()

    print(f"Cursos creados: {courses_created}")
    print(f"Profesores creados: {teachers_created}")
    print(f"Estudiantes creados: {students_created}")
    print(f"Asignaciones Profesor-curso creadas: {assignments_created}")
    print(f"Inscripciones creadas: {enrollments_created}")
    print(f"Tareas creadas: {tasks_created}")
    print(f"Entregas creadas: {submissions_created}")
    print(f"Entregas corregidas: {grades_created}")
    print("(Los registros existentes no se duplican.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
