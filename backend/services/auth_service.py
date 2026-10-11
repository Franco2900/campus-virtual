from flask import session
from werkzeug.security import check_password_hash

from models.base import db
from models.user import User


def authenticate_user(email, password):
    if not isinstance(email, str) or not email.strip():
        return None
    if not isinstance(password, str) or password == "":
        return None
    normalized_email = email.strip().lower()
    user = db.session.execute(
        db.select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()
    if user is None:
        return None
    if not user.active:
        return None
    if not check_password_hash(user.password_hash, password):
        return None
    return user


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None or not user.active:
        return None
    return user


def logout():
    session.clear()
