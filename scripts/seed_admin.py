"""Provisiona el Administrador inicial y datos de demostración del Campus Virtual.

Uso (desde la raíz del proyecto):
    Windows:  .\\.venv\\Scripts\\python.exe scripts\\seed_admin.py
    Linux/macOS: .venv/bin/python scripts/seed_admin.py

Requiere las variables de entorno CAMPUS_ADMIN_EMAIL y CAMPUS_ADMIN_PASSWORD.
Es idempotente: si el administrador ya existe, no duplica ni modifica nada.
"""

import os
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from models.base import db  # noqa: E402
from models.course import Course  # noqa: E402
from models.user import User, UserRole  # noqa: E402

ADMIN_EMAIL_ENV = "CAMPUS_ADMIN_EMAIL"
ADMIN_PASSWORD_ENV = "CAMPUS_ADMIN_PASSWORD"

DEMO_COURSES = [
    {
        "name": "Programación I",
        "code": "PROG1",
        "description": "Introducción a la programación y resolución de problemas.",
        "active": True,
    },
    {
        "name": "Matemática I",
        "code": "MAT1",
        "description": "Análisis matemático y álgebra para primer año.",
        "active": True,
    },
    {
        "name": "Historia",
        "code": "HIST1",
        "description": "Historia contemporánea (curso de demostración inactivo).",
        "active": False,
    },
    {
        "name": "Física",
        "code": "FIS1",
        "description": "Mecánica clásica y laboratorio.",
        "active": True,
    },
]


class SeedError(Exception):
    pass


def read_credentials(environ=None):
    environ = os.environ if environ is None else environ
    email = (environ.get(ADMIN_EMAIL_ENV) or "").strip()
    password = environ.get(ADMIN_PASSWORD_ENV) or ""
    missing = []
    if not email:
        missing.append(ADMIN_EMAIL_ENV)
    if not password:
        missing.append(ADMIN_PASSWORD_ENV)
    if missing:
        raise SeedError(
            "Faltan variables de entorno obligatorias: " + ", ".join(missing)
        )
    return email, password


def provision_admin(app, email, password, first_name="Admin", last_name="Sistema"):
    """Crea el administrador si no existe. Devuelve True si lo creó, False si ya existía."""
    with app.app_context():
        normalized_email = email.strip().lower()
        existing = db.session.execute(
            db.select(User).where(User.email == normalized_email)
        ).scalar_one_or_none()
        if existing is not None:
            return False
        admin = User(
            first_name=first_name,
            last_name=last_name,
            email=normalized_email,
            password_hash=generate_password_hash(password),
            role=UserRole.ADMIN,
        )
        db.session.add(admin)
        db.session.commit()
        return True


def seed_demo_courses(app):
    """Inserta los cursos de demostración que aún no existan. Devuelve cuántos creó."""
    created = 0
    with app.app_context():
        for spec in DEMO_COURSES:
            existing = db.session.execute(
                db.select(Course).where(Course.code == spec["code"])
            ).scalar_one_or_none()
            if existing is None:
                db.session.add(Course(**spec))
                created += 1
        db.session.commit()
    return created


def main():
    try:
        email, password = read_credentials()
    except SeedError as error:
        print(str(error), file=sys.stderr)
        return 1

    app = create_app()
    created = provision_admin(app, email, password)
    if not created:
        print("El administrador ya existe; no se realizan cambios.")
        return 0

    courses_created = seed_demo_courses(app)
    print(f"Administrador creado: {email.strip().lower()}")
    print(f"Cursos de demostración creados: {courses_created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
