from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services.errors import ConflictError, NotFoundError, ValidationError
from services.user_service import (
    get_user_or_404,
    list_users,
    reset_password,
    set_user_active,
    update_user,
)

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _serialize_user(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value,
        "active": user.active,
        "created_at": user.created_at.isoformat(),
    }


@users_bp.get("")
@login_required
@require_roles(UserRole.ADMIN)
def list_users_endpoint(current_user):
    try:
        users = list_users(
            q=request.args.get("q"),
            role=request.args.get("role"),
            active=request.args.get("active"),
        )
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify([_serialize_user(user) for user in users]), 200


@users_bp.get("/<int:user_id>")
@login_required
@require_roles(UserRole.ADMIN)
def get_user_endpoint(current_user, user_id):
    try:
        user = get_user_or_404(user_id)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_user(user)), 200


@users_bp.put("/<int:user_id>")
@login_required
@require_roles(UserRole.ADMIN)
def update_user_endpoint(current_user, user_id):
    data = request.get_json(silent=True)
    try:
        user = update_user(user_id, data, current_user=current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_user(user)), 200


@users_bp.patch("/<int:user_id>")
@login_required
@require_roles(UserRole.ADMIN)
def patch_user_endpoint(current_user, user_id):
    data = request.get_json(silent=True)
    active = data.get("active") if isinstance(data, dict) else None
    try:
        user = set_user_active(user_id, active, current_user=current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_user(user)), 200


@users_bp.post("/<int:user_id>/password")
@login_required
@require_roles(UserRole.ADMIN)
def reset_password_endpoint(current_user, user_id):
    data = request.get_json(silent=True)
    try:
        reset_password(user_id, data)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify({"message": "Contraseña actualizada"}), 200
