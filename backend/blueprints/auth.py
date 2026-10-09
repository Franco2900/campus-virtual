from flask import Blueprint, jsonify, request

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
