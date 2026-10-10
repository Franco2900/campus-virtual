from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services.course_service import (
    create_course,
    get_course_or_404,
    list_courses,
    set_course_active,
    update_course,
)
from services.errors import ConflictError, NotFoundError, ValidationError

courses_bp = Blueprint("courses", __name__, url_prefix="/api/courses")


def _serialize_course(course):
    return {
        "id": course.id,
        "name": course.name,
        "code": course.code,
        "description": course.description,
        "active": course.active,
        "created_at": course.created_at.isoformat(),
    }


@courses_bp.get("")
@login_required
@require_roles(UserRole.ADMIN)
def list_courses_endpoint(current_user):
    return jsonify([_serialize_course(course) for course in list_courses()]), 200


@courses_bp.post("")
@login_required
@require_roles(UserRole.ADMIN)
def create_course_endpoint(current_user):
    data = request.get_json(silent=True)
    try:
        course = create_course(data)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    return jsonify(_serialize_course(course)), 201


@courses_bp.get("/<int:course_id>")
@login_required
@require_roles(UserRole.ADMIN)
def get_course_endpoint(current_user, course_id):
    try:
        course = get_course_or_404(course_id)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_course(course)), 200


@courses_bp.put("/<int:course_id>")
@login_required
@require_roles(UserRole.ADMIN)
def update_course_endpoint(current_user, course_id):
    data = request.get_json(silent=True)
    try:
        course = update_course(course_id, data)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_course(course)), 200


@courses_bp.patch("/<int:course_id>")
@login_required
@require_roles(UserRole.ADMIN)
def patch_course_endpoint(current_user, course_id):
    data = request.get_json(silent=True)
    active = data.get("active") if isinstance(data, dict) else None
    try:
        course = set_course_active(course_id, active)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_course(course)), 200
