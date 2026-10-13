from datetime import datetime

from models.base import db
from models.task import Task
from services.course_service import get_manageable_course
from services.errors import ConflictError, NotFoundError, ValidationError

TITLE_MAX_LENGTH = 200


def _parse_due_date(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("La fecha límite es obligatoria o inválida")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        raise ValidationError("La fecha límite es obligatoria o inválida")


def _validate(data):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("El título es obligatorio")
    title = title.strip()
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError(f"El título no puede superar {TITLE_MAX_LENGTH} caracteres")

    description = data.get("description")
    if description is None:
        description = ""
    if not isinstance(description, str):
        raise ValidationError("La descripción debe ser texto")
    description = description.strip()

    due_date = _parse_due_date(data.get("due_date"))

    return title, description, due_date


def _get_task_or_404(course_id, task_id):
    task = db.session.execute(
        db.select(Task).where(Task.id == task_id, Task.course_id == course_id)
    ).scalar_one_or_none()
    if task is None:
        raise NotFoundError("La tarea no existe")
    return task


def list_tasks(course_id, current_user):
    get_manageable_course(course_id, current_user)
    return (
        db.session.execute(db.select(Task).where(Task.course_id == course_id).order_by(Task.id))
        .scalars()
        .all()
    )


def get_task(course_id, task_id, current_user):
    get_manageable_course(course_id, current_user)
    return _get_task_or_404(course_id, task_id)


def create_task(course_id, data, current_user):
    course = get_manageable_course(course_id, current_user)
    if not course.active:
        raise ConflictError("El curso está inactivo")

    title, description, due_date = _validate(data)
    task = Task(
        course_id=course_id,
        title=title,
        description=description,
        due_date=due_date,
        active=True,
    )
    db.session.add(task)
    db.session.commit()
    return task


def update_task(course_id, task_id, data, current_user):
    course = get_manageable_course(course_id, current_user)
    if not course.active:
        raise ConflictError("El curso está inactivo")

    title, description, due_date = _validate(data)
    task = _get_task_or_404(course_id, task_id)
    task.title = title
    task.description = description
    task.due_date = due_date
    db.session.commit()
    return task


def set_task_active(course_id, task_id, active, current_user):
    get_manageable_course(course_id, current_user)
    if not isinstance(active, bool):
        raise ValidationError("El campo active es obligatorio")

    task = _get_task_or_404(course_id, task_id)
    task.active = active
    db.session.commit()
    return task
