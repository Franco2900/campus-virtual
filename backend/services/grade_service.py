from models.base import db
from models.enrollment import Enrollment
from models.submission import Submission
from models.task import Task
from models.user import User, UserRole
from services.course_service import get_course_or_404, get_manageable_course
from services.errors import ForbiddenError
from services.grading_service import APPROVAL_THRESHOLD
from services.task_service import as_utc, now_utc


def _serialize_course(course):
    return {
        "id": course.id,
        "name": course.name,
        "code": course.code,
        "active": course.active,
    }


def _average(values):
    if not values:
        return None
    return sum(values) / len(values)


def _counted_value(task, submission):
    if not task.active:
        return None
    if submission is not None and submission.grade is not None:
        return submission.grade
    if submission is None and now_utc() > as_utc(task.due_date):
        return 1
    return None


def _active_tasks(course_id):
    return (
        db.session.execute(
            db.select(Task)
            .where(Task.course_id == course_id, Task.active.is_(True))
            .order_by(Task.id)
        )
        .scalars()
        .all()
    )


def _require_active_enrollment(course_id, current_user):
    enrollment = db.session.execute(
        db.select(Enrollment).where(
            Enrollment.course_id == course_id,
            Enrollment.student_id == current_user.id,
            Enrollment.active.is_(True),
        )
    ).scalar_one_or_none()
    if enrollment is None:
        raise ForbiddenError("No tenés una inscripción activa en este curso")


def _student_submissions(task_ids, student_id):
    if not task_ids:
        return {}
    rows = (
        db.session.execute(
            db.select(Submission).where(
                Submission.student_id == student_id,
                Submission.task_id.in_(task_ids),
            )
        )
        .scalars()
        .all()
    )
    return {submission.task_id: submission for submission in rows}


def _course_submissions(task_ids):
    if not task_ids:
        return {}
    rows = (
        db.session.execute(db.select(Submission).where(Submission.task_id.in_(task_ids)))
        .scalars()
        .all()
    )
    return {(submission.task_id, submission.student_id): submission for submission in rows}


def _serialize_student_task(task, submission, effective_value):
    grade = submission.grade if submission is not None else None
    corrected = grade is not None
    return {
        "task_id": task.id,
        "title": task.title,
        "due_date": task.due_date.isoformat(),
        "active": task.active,
        "submitted": submission is not None,
        "grade": grade,
        "feedback": submission.feedback if corrected else None,
        "graded_at": (
            submission.graded_at.isoformat()
            if corrected and submission.graded_at is not None
            else None
        ),
        "approved": corrected and grade >= APPROVAL_THRESHOLD,
        "counted": effective_value is not None,
        "effective_value": effective_value,
    }


def _student_view(course, current_user):
    _require_active_enrollment(course.id, current_user)

    tasks = _active_tasks(course.id)
    submissions = _student_submissions([task.id for task in tasks], current_user.id)

    contributing = []
    payloads = []
    for task in tasks:
        submission = submissions.get(task.id)
        effective_value = _counted_value(task, submission)
        if effective_value is not None:
            contributing.append(effective_value)
        payloads.append(_serialize_student_task(task, submission, effective_value))

    return {
        "course": _serialize_course(course),
        "average": _average(contributing),
        "tasks": payloads,
    }


def _teacher_view(course):
    tasks = _active_tasks(course.id)
    students = (
        db.session.execute(
            db.select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(
                Enrollment.course_id == course.id,
                Enrollment.active.is_(True),
            )
            .order_by(User.id)
        )
        .scalars()
        .all()
    )
    submissions = _course_submissions([task.id for task in tasks])

    student_payloads = []
    averages = []
    for student in students:
        grades = {}
        values = []
        for task in tasks:
            value = _counted_value(task, submissions.get((task.id, student.id)))
            grades[str(task.id)] = value
            if value is not None:
                values.append(value)
        average = _average(values)
        if average is not None:
            averages.append(average)
        student_payloads.append(
            {
                "student": {
                    "id": student.id,
                    "name": f"{student.first_name} {student.last_name}",
                    "email": student.email,
                },
                "grades": grades,
                "average": average,
            }
        )

    return {
        "course": _serialize_course(course),
        "tasks": [
            {
                "task_id": task.id,
                "title": task.title,
                "due_date": task.due_date.isoformat(),
                "active": task.active,
            }
            for task in tasks
        ],
        "students": student_payloads,
        "course_average": _average(averages),
    }


def get_course_grades(course_id, current_user):
    if current_user.role == UserRole.STUDENT:
        course = get_course_or_404(course_id)
        return _student_view(course, current_user)
    course = get_manageable_course(course_id, current_user)
    return _teacher_view(course)
