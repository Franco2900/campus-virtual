import re

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from models.base import db
from models.user import User, UserRole
from services.errors import ConflictError, ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
IDENTITY_FIELDS = ("first_name", "last_name", "email")
FIELD_LABELS = {
    "first_name": "nombre",
    "last_name": "apellido",
    "email": "correo electrónico",
}


def register_user(data):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    values = {}
    for field in IDENTITY_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"El campo {FIELD_LABELS[field]} es obligatorio")
        values[field] = value.strip()

    password = data.get("password")
    if not isinstance(password, str) or password == "":
        raise ValidationError("La contraseña es obligatoria")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        )

    email = values["email"].lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("El formato del correo electrónico es inválido")

    existing = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("El correo electrónico ya está registrado")

    user = User(
        first_name=values["first_name"],
        last_name=values["last_name"],
        email=email,
        password_hash=generate_password_hash(password),
        role=UserRole.STUDENT,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("El correo electrónico ya está registrado")
    return user
