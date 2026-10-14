from sqlalchemy.exc import IntegrityError

from models.base import db
from models.enrollment import Enrollment
from models.submission import Submission
from models.task import Task
from services.course_service import get_course_or_404
from services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from services.task_service import ensure_task_available, get_task_or_404

CONTENT_MAX_LENGTH = 5000
LINK_MAX_LENGTH = 500
LINKS_MAX_COUNT = 10


def _require_enrollment(course_id, current_user):
    enrollment = db.session.execute(
        db.select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == current_user.id,
            Enrollment.active.is_(True),
        )
    ).scalar_one_or_none()
    if enrollment is None:
        raise ForbiddenError("No tenés una inscripción activa en este curso")


def _get_submission_or_404(task_id, student_id):
    submission = get_submission_for_student(task_id, student_id)
    if submission is None:
        raise NotFoundError("La entrega no existe")
    return submission


def _validate(data):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    content = data.get("content")
    if content is None:
        content = ""
    if not isinstance(content, str):
        raise ValidationError("El contenido debe ser texto")
    content = content.strip()
    if len(content) > CONTENT_MAX_LENGTH:
        raise ValidationError(f"El contenido no puede superar {CONTENT_MAX_LENGTH} caracteres")

    links = data.get("links")
    if links is None:
        links = []
    if not isinstance(links, list):
        raise ValidationError("Los enlaces deben ser una lista")

    normalized_links = []
    for link in links:
        if not isinstance(link, str):
            raise ValidationError("Cada enlace debe ser texto")
        link = link.strip()
        if not link:
            continue
        if len(link) > LINK_MAX_LENGTH:
            raise ValidationError(f"Cada enlace no puede superar {LINK_MAX_LENGTH} caracteres")
        normalized_links.append(link)

    if len(normalized_links) > LINKS_MAX_COUNT:
        raise ValidationError(f"No se pueden enviar más de {LINKS_MAX_COUNT} enlaces")

    if not content and not normalized_links:
        raise ValidationError("La entrega debe incluir texto o al menos un enlace")

    return content, normalized_links


def get_submission_for_student(task_id, student_id):
    return db.session.execute(
        db.select(Submission).where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
        )
    ).scalar_one_or_none()


def list_submissions_for_student(course_id, student_id):
    return (
        db.session.execute(
            db.select(Submission)
            .join(Task, Task.id == Submission.task_id)
            .where(Task.course_id == course_id, Submission.student_id == student_id)
            .order_by(Submission.task_id)
        )
        .scalars()
        .all()
    )


def create_submission(course_id, task_id, data, current_user):
    get_course_or_404(course_id)
    _require_enrollment(course_id, current_user)
    task = get_task_or_404(course_id, task_id)
    ensure_task_available(task)
    content, links = _validate(data)

    if get_submission_for_student(task_id, current_user.id) is not None:
        raise ConflictError("Ya entregaste esta tarea")

    submission = Submission(
        task_id=task_id,
        student_id=current_user.id,
        content=content,
        links=links,
    )
    db.session.add(submission)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Ya entregaste esta tarea")
    return submission


def update_submission(course_id, task_id, data, current_user):
    get_course_or_404(course_id)
    _require_enrollment(course_id, current_user)
    task = get_task_or_404(course_id, task_id)
    ensure_task_available(task)
    content, links = _validate(data)

    submission = _get_submission_or_404(task_id, current_user.id)
    if submission.grade is not None:
        raise ConflictError("La entrega ya fue corregida")
    submission.content = content
    submission.links = links
    db.session.commit()
    return submission


def delete_submission(course_id, task_id, current_user):
    get_course_or_404(course_id)
    _require_enrollment(course_id, current_user)
    task = get_task_or_404(course_id, task_id)
    ensure_task_available(task)

    submission = _get_submission_or_404(task_id, current_user.id)
    if submission.grade is not None:
        raise ConflictError("La entrega ya fue corregida")
    db.session.delete(submission)
    db.session.commit()
