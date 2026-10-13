from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import course_teacher_service
from services.course_service import (
    create_course,
    get_course_or_404,
    list_courses,
    list_courses_for_user,
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


def _serialize_teacher(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value,
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


@courses_bp.get("/mine")
@login_required
@require_roles(UserRole.ADMIN, UserRole.TEACHER, UserRole.STUDENT)
def list_my_courses_endpoint(current_user):
    return jsonify(
        [_serialize_course(course) for course in list_courses_for_user(current_user)]
    ), 200


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


@courses_bp.get("/<int:course_id>/teachers")
@login_required
@require_roles(UserRole.ADMIN)
def list_teachers_endpoint(current_user, course_id):
    try:
        teachers = course_teacher_service.list_teachers(course_id)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify([_serialize_teacher(teacher) for teacher in teachers]), 200


@courses_bp.post("/<int:course_id>/teachers")
@login_required
@require_roles(UserRole.ADMIN)
def assign_teacher_endpoint(current_user, course_id):
    data = request.get_json(silent=True)
    teacher_id = data.get("teacher_id") if isinstance(data, dict) else None
    try:
        teacher = course_teacher_service.assign_teacher(course_id, teacher_id)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify(_serialize_teacher(teacher)), 201


@courses_bp.delete("/<int:course_id>/teachers/<int:teacher_id>")
@login_required
@require_roles(UserRole.ADMIN)
def remove_teacher_endpoint(current_user, course_id, teacher_id):
    try:
        course_teacher_service.remove_teacher(course_id, teacher_id)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    return jsonify({"message": "Profesor desasignado"}), 200
