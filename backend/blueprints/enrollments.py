from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import enrollment_service
from services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError

enrollments_bp = Blueprint("enrollments", __name__, url_prefix="/api/courses")


def _serialize_enrollment(enrollment):
    if enrollment is None:
        return None
    return {
        "id": enrollment.id,
        "active": enrollment.active,
        "enrolled_at": enrollment.enrolled_at.isoformat(),
    }


def _serialize_student(user, enrollment):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value,
        "enrollment": _serialize_enrollment(enrollment),
    }


@enrollments_bp.get("/<int:course_id>/students")
@login_required
@require_roles(UserRole.ADMIN, UserRole.TEACHER)
def list_students_endpoint(current_user, course_id):
    try:
        rows = enrollment_service.list_students(course_id, current_user)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify([_serialize_student(user, enrollment) for user, enrollment in rows]), 200


@enrollments_bp.post("/<int:course_id>/students")
@login_required
@require_roles(UserRole.ADMIN, UserRole.TEACHER)
def enroll_student_endpoint(current_user, course_id):
    data = request.get_json(silent=True)
    student_id = data.get("student_id") if isinstance(data, dict) else None
    try:
        student, enrollment = enrollment_service.enroll_student(course_id, student_id, current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_student(student, enrollment)), 201


@enrollments_bp.patch("/<int:course_id>/students/<int:student_id>")
@login_required
@require_roles(UserRole.ADMIN, UserRole.TEACHER)
def set_enrollment_active_endpoint(current_user, course_id, student_id):
    data = request.get_json(silent=True)
    active = data.get("active") if isinstance(data, dict) else None
    try:
        student, enrollment = enrollment_service.set_enrollment_active(
            course_id, student_id, active, current_user
        )
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_student(student, enrollment)), 200


@enrollments_bp.delete("/<int:course_id>/students/<int:student_id>")
@login_required
@require_roles(UserRole.ADMIN, UserRole.TEACHER)
def remove_enrollment_endpoint(current_user, course_id, student_id):
    try:
        enrollment_service.remove_enrollment(course_id, student_id, current_user)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify({"message": "Inscripción eliminada"}), 200
