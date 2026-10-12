"""Provisiona datos de demostración ampliados del Campus Virtual.

Crea Profesores, Estudiantes (uno inactivo), asignaciones Profesor↔curso e
inscripciones (activas e inactivas) sobre los cursos demo ya sembrados por
`scripts/seed_admin.py`. Es idempotente: cada registro se busca por su clave
natural (email, par curso+profesor, par curso+estudiante) antes de insertarse.

Uso (desde la raíz del proyecto, con el Administrador y los cursos demo ya creados):
    Windows:     .\\.venv\\Scripts\\python.exe scripts\\seed_demo.py
    Linux/macOS: .venv/bin/python scripts/seed_demo.py

Contraseñas de demo (se pueden sobreescribir por entorno):
    CAMPUS_DEMO_TEACHER_PASSWORD (default "Docente123")
    CAMPUS_DEMO_STUDENT_PASSWORD (default "Alumno123")
"""

import os
import sys
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
from models.user import User, UserRole  # noqa: E402

TEACHER_PASSWORD_ENV = "CAMPUS_DEMO_TEACHER_PASSWORD"
STUDENT_PASSWORD_ENV = "CAMPUS_DEMO_STUDENT_PASSWORD"
DEFAULT_TEACHER_PASSWORD = "Docente123"
DEFAULT_STUDENT_PASSWORD = "Alumno123"

DEMO_TEACHERS = [
    {"first_name": "Laura", "last_name": "Gómez", "email": "docente1@campus.edu"},
    {"first_name": "Martín", "last_name": "Pérez", "email": "docente2@campus.edu"},
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
]

# (teacher_email, course_code)
DEMO_ASSIGNMENTS = [
    ("docente1@campus.edu", "PROG1"),
    ("docente1@campus.edu", "MAT1"),
    ("docente2@campus.edu", "FIS1"),
    ("docente2@campus.edu", "PROG1"),
]

# (student_email, course_code, active) — solo cursos y cuentas activos
DEMO_ENROLLMENTS = [
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


def _get_user(email):
    return db.session.execute(
        db.select(User).where(User.email == email.strip().lower())
    ).scalar_one_or_none()


def _get_course(code):
    return db.session.execute(
        db.select(Course).where(Course.code == code)
    ).scalar_one_or_none()


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

        teachers_created = _seed_users(
            DEMO_TEACHERS, UserRole.TEACHER, generate_password_hash(teacher_password)
        )
        students_created = _seed_users(
            DEMO_STUDENTS, UserRole.STUDENT, generate_password_hash(student_password)
        )
        assignments_created = _seed_assignments(DEMO_ASSIGNMENTS)
        enrollments_created = _seed_enrollments(DEMO_ENROLLMENTS)

    print(f"Profesores creados: {teachers_created}")
    print(f"Estudiantes creados: {students_created}")
    print(f"Asignaciones Profesor-curso creadas: {assignments_created}")
    print(f"Inscripciones creadas: {enrollments_created}")
    print("(Los registros existentes no se duplican.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
