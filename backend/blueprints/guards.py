import functools

from flask import jsonify

from services.auth_service import get_current_user


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = get_current_user()
        if current_user is None:
            return jsonify({"error": "Iniciar sesión para acceder a este recurso"}), 401
        return f(*args, current_user=current_user, **kwargs)

    return decorated_function


def require_roles(*roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, current_user=None, **kwargs):
            if current_user is None:
                return jsonify({"error": "No tenés permisos para realizar esta acción"}), 403
            user_role = (
                current_user.role.value
                if hasattr(current_user.role, "value")
                else str(current_user.role)
            )
            role_values = []
            for role in roles:
                role_values.append(role.value if hasattr(role, "value") else str(role))
            if user_role not in role_values:
                return jsonify({"error": "No tenés permisos para realizar esta acción"}), 403
            return f(*args, current_user=current_user, **kwargs)

        return decorated_function

    return decorator
