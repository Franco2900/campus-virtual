from flask import Blueprint, jsonify, request, session

from blueprints.guards import login_required
from services.auth_service import authenticate_user, logout
from services.errors import ConflictError, ValidationError
from services.user_service import register_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _serialize_user(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value,
    }


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "El cuerpo de la solicitud debe ser un objeto JSON"}), 400

    try:
        user = register_user(data)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409

    return jsonify(_serialize_user(user)), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "El campo correo electrónico es obligatorio"}), 400
    if not isinstance(password, str) or password == "":
        return jsonify({"error": "La contraseña es obligatoria"}), 400

    user = authenticate_user(email, password)
    if user is None:
        return jsonify({"error": "El correo electrónico o la contraseña son incorrectos"}), 401

    session["user_id"] = user.id
    return jsonify(_serialize_user(user)), 200


@auth_bp.get("/me")
@login_required
def me(current_user):
    return jsonify(_serialize_user(current_user)), 200


@auth_bp.post("/logout")
def logout_endpoint():
    logout()
    return jsonify({"message": "Sesión cerrada"}), 200
