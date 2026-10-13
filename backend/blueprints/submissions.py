from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import submission_service
from services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError

submissions_bp = Blueprint("submissions", __name__, url_prefix="/api/courses")


def _serialize_submission(submission):
    if submission is None:
        return None
    return {
        "id": submission.id,
        "task_id": submission.task_id,
        "content": submission.content,
        "links": submission.links,
        "updated_at": submission.updated_at.isoformat(),
    }


@submissions_bp.post("/<int:course_id>/tasks/<int:task_id>/submission")
@login_required
@require_roles(UserRole.STUDENT)
def create_submission_endpoint(current_user, course_id, task_id):
    data = request.get_json(silent=True)
    try:
        submission = submission_service.create_submission(course_id, task_id, data, current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_submission(submission)), 201


@submissions_bp.put("/<int:course_id>/tasks/<int:task_id>/submission")
@login_required
@require_roles(UserRole.STUDENT)
def update_submission_endpoint(current_user, course_id, task_id):
    data = request.get_json(silent=True)
    try:
        submission = submission_service.update_submission(course_id, task_id, data, current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_submission(submission)), 200


@submissions_bp.delete("/<int:course_id>/tasks/<int:task_id>/submission")
@login_required
@require_roles(UserRole.STUDENT)
def delete_submission_endpoint(current_user, course_id, task_id):
    try:
        submission_service.delete_submission(course_id, task_id, current_user)
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify({"message": "Entrega eliminada"}), 200
