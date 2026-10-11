import re

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from models.base import db
from models.user import User, UserRole
from services.errors import ConflictError, NotFoundError, ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
IDENTITY_FIELDS = ("first_name", "last_name", "email")
FIELD_LABELS = {
    "first_name": "nombre",
    "last_name": "apellido",
    "email": "correo electrónico",
}
ROLE_VALUES = {role.value: role for role in UserRole}


def _clean_identity(data):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    values = {}
    for field in IDENTITY_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"El campo {FIELD_LABELS[field]} es obligatorio")
        values[field] = value.strip()

    email = values["email"].lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("El formato del correo electrónico es inválido")

    return values["first_name"], values["last_name"], email


def _clean_password(password):
    if not isinstance(password, str) or password == "":
        raise ValidationError("La contraseña es obligatoria")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
    return password


def _parse_role(value):
    if isinstance(value, UserRole):
        return value
    if isinstance(value, str):
        role = ROLE_VALUES.get(value.strip().lower())
        if role is not None:
            return role
    raise ValidationError("El rol es inválido")


def _email_in_use(email, exclude_id=None):
    query = db.select(User).where(User.email == email)
    if exclude_id is not None:
        query = query.where(User.id != exclude_id)
    return db.session.execute(query).scalar_one_or_none() is not None


def register_user(data):
    first_name, last_name, email = _clean_identity(data)
    password = _clean_password(data.get("password"))

    if _email_in_use(email):
        raise ConflictError("El correo electrónico ya está registrado")

    user = User(
        first_name=first_name,
        last_name=last_name,
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


def list_users():
    return db.session.execute(db.select(User).order_by(User.id)).scalars().all()


def get_user_or_404(user_id):
    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise NotFoundError("El usuario no existe")
    return user


def update_user(user_id, data, current_user=None):
    user = get_user_or_404(user_id)
    first_name, last_name, email = _clean_identity(data)
    role = _parse_role(data.get("role"))

    if current_user is not None and current_user.id == user.id and role != UserRole.ADMIN:
        raise ValidationError("No puede cambiar su propio rol")

    if _email_in_use(email, exclude_id=user.id):
        raise ConflictError("El correo electrónico ya está registrado")

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.role = role
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("El correo electrónico ya está registrado")
    return user


def set_user_active(user_id, active, current_user=None):
    user = get_user_or_404(user_id)
    if not isinstance(active, bool):
        raise ValidationError("El campo active debe ser booleano")
    if current_user is not None and current_user.id == user.id and active is False:
        raise ValidationError("No puede desactivar su propia cuenta")
    user.active = active
    db.session.commit()
    return user


def reset_password(user_id, data):
    user = get_user_or_404(user_id)
    password = data.get("password") if isinstance(data, dict) else None
    password = _clean_password(password)
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    return user
