from datetime import UTC, datetime, timedelta

from werkzeug.security import generate_password_hash

from models.base import db
from models.course import Course
from models.course_teacher import CourseTeacher
from models.enrollment import Enrollment
from models.submission import Submission
from models.task import Task
from models.user import User, UserRole

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
STUDENT_TWO = {"email": "student2@example.com", "password": "student2pass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}

GRADING_FIELDS = {
    "id",
    "task_id",
    "student_id",
    "content",
    "links",
    "grade",
    "feedback",
    "graded_at",
    "approved",
}
LIST_FIELDS = GRADING_FIELDS | {"student"}
STUDENT_FIELDS = {"id", "first_name", "last_name", "name", "email"}
PAST_DUE_DATE = datetime(2020, 1, 1, tzinfo=UTC)


def _create_user(app, credentials, role, active=True, first_name="Nombre", last_name="Apellido"):
    with app.app_context():
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=credentials["email"].lower(),
            password_hash=generate_password_hash(credentials["password"]),
            role=role,
            active=active,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, credentials):
    return client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )


def _seed_course(app, code="PROG1", active=True):
    with app.app_context():
        course = Course(name="Programación I", code=code, description="", active=active)
        db.session.add(course)
        db.session.commit()
        return course.id


def _assign_teacher(app, course_id, teacher_id):
    with app.app_context():
        db.session.add(CourseTeacher(course_id=course_id, teacher_id=teacher_id))
        db.session.commit()


def _seed_enrollment(app, course_id, student_id, active=True):
    with app.app_context():
        enrollment = Enrollment(course_id=course_id, student_id=student_id, active=active)
        db.session.add(enrollment)
        db.session.commit()
        return enrollment.id


def _seed_task(app, course_id, title="Tarea 1", due_date=None, active=True):
    if due_date is None:
        due_date = datetime.now(UTC) + timedelta(days=30)
    with app.app_context():
        task = Task(
            course_id=course_id,
            title=title,
            description="",
            due_date=due_date,
            active=active,
        )
        db.session.add(task)
        db.session.commit()
        return task.id


def _seed_submission(
    app,
    task_id,
    student_id,
    content="Entrega",
    links=None,
    grade=None,
    feedback="",
    graded_at=None,
):
    with app.app_context():
        submission = Submission(
            task_id=task_id,
            student_id=student_id,
            content=content,
            links=links if links is not None else [],
            grade=grade,
            feedback=feedback,
            graded_at=graded_at,
        )
        db.session.add(submission)
        db.session.commit()
        return submission.id


def _list_url(course_id, task_id):
    return f"/api/courses/{course_id}/tasks/{task_id}/submissions"


def _grade_url(course_id, task_id, student_id):
    return f"/api/courses/{course_id}/tasks/{task_id}/submissions/{student_id}/grade"


def _teacher_with_course(client, app, code="PROG1"):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, code=code)
    _assign_teacher(app, course_id, teacher_id)
    _login(client, TEACHER)
    return teacher_id, course_id


def test_grading_requires_session(client, app):
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    assert client.get(_list_url(course_id, task_id)).status_code == 401
    assert client.put(_grade_url(course_id, task_id, 1), json={"grade": 8}).status_code == 401


def test_list_submissions_forbidden_for_student(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, STUDENT)
    assert client.get(_list_url(course_id, task_id)).status_code == 403


def test_list_submissions_forbidden_for_admin(client, app):
    _create_user(app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, ADMIN)
    assert client.get(_list_url(course_id, task_id)).status_code == 403


def test_list_submissions_course_not_found(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    _login(client, TEACHER)
    assert client.get(_list_url(9999, 1)).status_code == 404


def test_list_submissions_forbidden_when_not_assigned(client, app):
    other_teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, TEACHER)
    assert other_teacher_id > 0
    assert client.get(_list_url(course_id, task_id)).status_code == 403


def test_list_submissions_task_not_found(client, app):
    _, course_id = _teacher_with_course(client, app)
    assert client.get(_list_url(course_id, 9999)).status_code == 404


def test_list_submissions_task_from_other_course(client, app):
    _, course_id = _teacher_with_course(client, app, code="PROG1")
    other_course_id = _seed_course(app, code="PROG2")
    other_task_id = _seed_task(app, other_course_id, title="De otro curso")
    assert client.get(_list_url(course_id, other_task_id)).status_code == 404


def test_list_submissions_success(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT, first_name="Ana", last_name="Díaz")
    _seed_submission(app, task_id, student_id, content="Mi entrega")

    response = client.get(_list_url(course_id, task_id))
    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert set(body[0]) == LIST_FIELDS
    assert body[0]["student_id"] == student_id
    assert set(body[0]["student"]) == STUDENT_FIELDS
    assert body[0]["student"]["name"] == "Ana Díaz"
    assert body[0]["student"]["email"] == STUDENT["email"]
    assert body[0]["content"] == "Mi entrega"
    assert body[0]["grade"] is None
    assert body[0]["graded_at"] is None
    assert body[0]["approved"] is False


def test_list_submissions_without_enrollment_is_allowed(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id, content="Sin inscripción")
    response = client.get(_list_url(course_id, task_id))
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_grade_forbidden_for_student(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _seed_submission(app, task_id, student_id)
    _login(client, STUDENT)
    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 8}).status_code == 403
    )


def test_grade_forbidden_for_admin(client, app):
    _create_user(app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, ADMIN)
    assert client.put(_grade_url(course_id, task_id, 1), json={"grade": 8}).status_code == 403


def test_grade_course_not_found(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    _login(client, TEACHER)
    assert client.put(_grade_url(9999, 1, 1), json={"grade": 8}).status_code == 404


def test_grade_forbidden_when_not_assigned(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)
    _login(client, TEACHER)
    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 8}).status_code == 403
    )


def test_grade_task_not_found(client, app):
    _, course_id = _teacher_with_course(client, app)
    assert client.put(_grade_url(course_id, 9999, 1), json={"grade": 8}).status_code == 404


def test_grade_task_from_other_course(client, app):
    _, course_id = _teacher_with_course(client, app, code="PROG1")
    other_course_id = _seed_course(app, code="PROG2")
    other_task_id = _seed_task(app, other_course_id, title="De otro curso")
    assert client.put(_grade_url(course_id, other_task_id, 1), json={"grade": 8}).status_code == 404


def test_grade_submission_not_found(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 8}).status_code == 404
    )


def test_grade_submission_without_enrollment_is_allowed(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)
    response = client.put(_grade_url(course_id, task_id, student_id), json={"grade": 7})
    assert response.status_code == 200


def test_grade_submission_success(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)

    response = client.put(
        _grade_url(course_id, task_id, student_id),
        json={"grade": 9, "feedback": "  Muy bien  "},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == GRADING_FIELDS
    assert body["grade"] == 9
    assert body["feedback"] == "Muy bien"
    assert body["graded_at"] is not None
    assert body["approved"] is True


def test_grade_submission_invalid_values(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)

    for invalid in (0, 11, 7.5, "8", True, None, "abc"):
        response = client.put(_grade_url(course_id, task_id, student_id), json={"grade": invalid})
        assert response.status_code == 400, invalid

    with app.app_context():
        submission = db.session.execute(
            db.select(Submission).where(
                Submission.task_id == task_id, Submission.student_id == student_id
            )
        ).scalar_one()
        assert submission.grade is None


def test_grade_submission_feedback_too_long(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)

    response = client.put(
        _grade_url(course_id, task_id, student_id),
        json={"grade": 8, "feedback": "x" * 5001},
    )
    assert response.status_code == 400


def test_grade_submission_feedback_exact_limit(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)

    response = client.put(
        _grade_url(course_id, task_id, student_id),
        json={"grade": 8, "feedback": "x" * 5000},
    )
    assert response.status_code == 200
    assert response.get_json()["feedback"] == "x" * 5000


def test_grade_submission_update_existing_grade(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    old_graded_at = datetime(2020, 1, 1, tzinfo=UTC)
    _seed_submission(app, task_id, student_id, grade=4, feedback="Regular", graded_at=old_graded_at)
    old_graded_at_naive = old_graded_at.replace(tzinfo=None)

    response = client.put(
        _grade_url(course_id, task_id, student_id),
        json={"grade": 8, "feedback": "Mejoró"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["grade"] == 8
    assert body["feedback"] == "Mejoró"
    assert body["approved"] is True
    assert datetime.fromisoformat(body["graded_at"]) > old_graded_at_naive


def test_grade_approved_threshold(client, app):
    _, course_id = _teacher_with_course(client, app)
    task_id = _seed_task(app, course_id)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_submission(app, task_id, student_id)

    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 6}).get_json()[
            "approved"
        ]
        is True
    )
    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 10}).get_json()[
            "approved"
        ]
        is True
    )
    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 5}).get_json()[
            "approved"
        ]
        is False
    )
    assert (
        client.put(_grade_url(course_id, task_id, student_id), json={"grade": 1}).get_json()[
            "approved"
        ]
        is False
    )


def test_student_cannot_update_graded_submission(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id)
    task_id = _seed_task(app, course_id)
    _seed_submission(
        app, task_id, student_id, content="Original", grade=8, graded_at=datetime.now(UTC)
    )
    _login(client, STUDENT)

    response = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}/submission", json={"content": "Cambio"}
    )
    assert response.status_code == 409

    with app.app_context():
        submission = db.session.execute(
            db.select(Submission).where(Submission.student_id == student_id)
        ).scalar_one()
        assert submission.content == "Original"


def test_student_cannot_delete_graded_submission(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id)
    task_id = _seed_task(app, course_id)
    _seed_submission(app, task_id, student_id, grade=8, graded_at=datetime.now(UTC))
    _login(client, STUDENT)

    response = client.delete(f"/api/courses/{course_id}/tasks/{task_id}/submission")
    assert response.status_code == 409

    with app.app_context():
        submission = db.session.execute(
            db.select(Submission).where(Submission.student_id == student_id)
        ).scalar_one_or_none()
        assert submission is not None


def test_student_can_update_and_delete_ungraded_submission(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id)
    task_id = _seed_task(app, course_id)
    _seed_submission(app, task_id, student_id, content="Original")
    _login(client, STUDENT)

    update = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}/submission", json={"content": "Cambio"}
    )
    assert update.status_code == 200
    assert update.get_json()["content"] == "Cambio"

    delete = client.delete(f"/api/courses/{course_id}/tasks/{task_id}/submission")
    assert delete.status_code == 200


def test_student_own_submission_serialization_hides_grading(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id)
    task_id = _seed_task(app, course_id)
    _seed_submission(app, task_id, student_id, content="Mía", grade=9, graded_at=datetime.now(UTC))
    _login(client, STUDENT)

    response = client.get(f"/api/courses/{course_id}/tasks")
    assert response.status_code == 200
    submission = response.get_json()[0]["submission"]
    assert submission is not None
    assert "grade" not in submission
    assert "feedback" not in submission
    assert "graded_at" not in submission
