from flask import Blueprint, jsonify, request

from blueprints.guards import login_required, require_roles
from models.user import UserRole
from services import task_service
from services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/courses")


def _serialize_task(task, submission=None, include_submission=False):
    data = {
        "id": task.id,
        "course_id": task.course_id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat(),
        "active": task.active,
    }
    if include_submission:
        data["submission"] = _serialize_submission(submission)
    return data


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


@tasks_bp.get("/<int:course_id>/tasks")
@login_required
@require_roles(UserRole.TEACHER, UserRole.STUDENT)
def list_tasks_endpoint(current_user, course_id):
    include_submission = current_user.role == UserRole.STUDENT
    try:
        rows = task_service.list_tasks(course_id, current_user)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return (
        jsonify(
            [_serialize_task(task, submission, include_submission) for task, submission in rows]
        ),
        200,
    )


@tasks_bp.post("/<int:course_id>/tasks")
@login_required
@require_roles(UserRole.TEACHER)
def create_task_endpoint(current_user, course_id):
    data = request.get_json(silent=True)
    try:
        task = task_service.create_task(course_id, data, current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_task(task)), 201


@tasks_bp.get("/<int:course_id>/tasks/<int:task_id>")
@login_required
@require_roles(UserRole.TEACHER)
def get_task_endpoint(current_user, course_id, task_id):
    try:
        task = task_service.get_task(course_id, task_id, current_user)
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_task(task)), 200


@tasks_bp.put("/<int:course_id>/tasks/<int:task_id>")
@login_required
@require_roles(UserRole.TEACHER)
def update_task_endpoint(current_user, course_id, task_id):
    data = request.get_json(silent=True)
    try:
        task = task_service.update_task(course_id, task_id, data, current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except ConflictError as error:
        return jsonify({"error": str(error)}), 409
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_task(task)), 200


@tasks_bp.patch("/<int:course_id>/tasks/<int:task_id>")
@login_required
@require_roles(UserRole.TEACHER)
def set_task_active_endpoint(current_user, course_id, task_id):
    data = request.get_json(silent=True)
    active = data.get("active") if isinstance(data, dict) else None
    try:
        task = task_service.set_task_active(course_id, task_id, active, current_user)
    except ValidationError as error:
        return jsonify({"error": str(error)}), 400
    except NotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except ForbiddenError as error:
        return jsonify({"error": str(error)}), 403
    return jsonify(_serialize_task(task)), 200
