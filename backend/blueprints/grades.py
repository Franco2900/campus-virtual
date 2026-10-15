from flask import Blueprint, jsonify

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import grade_service
from services.errors import ForbiddenError, NotFoundError

grades_bp = Blueprint("grades", __name__, url_prefix="/api/courses")


@grades_bp.get("/<int:course_id>/grades")
@login_required
@require_roles(UserRole.TEACHER, UserRole.STUDENT)
def get_course_grades_endpoint(current_user, course_id):
    try:
        payload = grade_service.get_course_grades(course_id, current_user)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(payload), 200
