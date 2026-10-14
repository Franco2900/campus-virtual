from datetime import UTC, datetime

from models.base import db
from models.submission import Submission
from models.user import User
from services.course_service import get_manageable_course
from services.errors import NotFoundError, ValidationError
from services.task_service import get_task_or_404

FEEDBACK_MAX_LENGTH = 5000
GRADE_MIN = 1
GRADE_MAX = 10
APPROVAL_THRESHOLD = 6
GRADE_ERROR = "La calificación debe ser un entero entre 1 y 10"


def _is_approved(grade):
    return grade is not None and grade >= APPROVAL_THRESHOLD


def serialize_submission(submission, student=None):
    payload = {
        "id": submission.id,
        "task_id": submission.task_id,
        "student_id": submission.student_id,
        "content": submission.content,
        "links": submission.links,
        "grade": submission.grade,
        "feedback": submission.feedback,
        "graded_at": submission.graded_at.isoformat() if submission.graded_at else None,
        "approved": _is_approved(submission.grade),
    }
    if student is not None:
        payload["student"] = {
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "name": f"{student.first_name} {student.last_name}",
            "email": student.email,
        }
    return payload


def _validate_grade(data):
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo de la solicitud debe ser un objeto JSON")

    grade = data.get("grade")
    if isinstance(grade, bool) or not isinstance(grade, int):
        raise ValidationError(GRADE_ERROR)
    if grade < GRADE_MIN or grade > GRADE_MAX:
        raise ValidationError(GRADE_ERROR)

    feedback = data.get("feedback")
    if feedback is None:
        feedback = ""
    if not isinstance(feedback, str):
        raise ValidationError("La retroalimentación debe ser texto")
    feedback = feedback.strip()
    if len(feedback) > FEEDBACK_MAX_LENGTH:
        raise ValidationError(
            f"La retroalimentación no puede superar {FEEDBACK_MAX_LENGTH} caracteres"
        )

    return grade, feedback


def _get_submission_or_404(task_id, student_id):
    submission = db.session.execute(
        db.select(Submission).where(
            Submission.task_id == task_id,
            Submission.student_id == student_id,
        )
    ).scalar_one_or_none()
    if submission is None:
        raise NotFoundError("La entrega no existe")
    return submission


def list_submissions_for_task(course_id, task_id, current_user):
    get_manageable_course(course_id, current_user)
    get_task_or_404(course_id, task_id)

    rows = db.session.execute(
        db.select(Submission, User)
        .join(User, User.id == Submission.student_id)
        .where(Submission.task_id == task_id)
        .order_by(Submission.student_id)
    ).all()
    return [serialize_submission(submission, student) for submission, student in rows]


def grade_submission(course_id, task_id, student_id, data, current_user):
    get_manageable_course(course_id, current_user)
    get_task_or_404(course_id, task_id)
    submission = _get_submission_or_404(task_id, student_id)

    grade, feedback = _validate_grade(data)
    submission.grade = grade
    submission.feedback = feedback
    submission.graded_at = datetime.now(UTC)
    db.session.commit()
    return submission
