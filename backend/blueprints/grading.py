from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import grading_service
from services.errors import ForbiddenError, NotFoundError, ValidationError

grading_bp = Blueprint("grading", __name__, url_prefix="/api/courses")


@grading_bp.get("/<int:course_id>/tasks/<int:task_id>/submissions")
@login_required
@require_roles(UserRole.TEACHER)
def list_submissions_endpoint(current_user, course_id, task_id):
    try:
        rows = grading_service.list_submissions_for_task(course_id, task_id, current_user)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(rows), 200


@grading_bp.put("/<int:course_id>/tasks/<int:task_id>/submissions/<int:student_id>/grade")
@login_required
@require_roles(UserRole.TEACHER)
def grade_submission_endpoint(current_user, course_id, task_id, student_id):
    data = request.get_json(silent=True)
    try:
        submission = grading_service.grade_submission(
            course_id, task_id, student_id, data, current_user
        )
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(grading_service.serialize_submission(submission)), 200
