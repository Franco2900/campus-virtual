from datetime import UTC, datetime, timedelta

from werkzeug.security import generate_password_hash

from models.base import db
from models.course import Course
from models.enrollment import Enrollment
from models.submission import Submission
from models.task import Task
from models.user import User, UserRole

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
STUDENT_TWO = {"email": "student2@example.com", "password": "student2pass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}

FUTURE_DUE_DATE = "2026-12-01T10:00:00"
PAST_DUE_DATE = "2020-01-01T00:00:00"
TASK_FIELDS = {"id", "course_id", "title", "description", "due_date", "active"}
STUDENT_TASK_FIELDS = TASK_FIELDS | {"submission"}
SUBMISSION_FIELDS = {"id", "task_id", "content", "links", "updated_at"}


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


def _seed_submission(app, task_id, student_id, content="Entrega", links=None):
    with app.app_context():
        submission = Submission(
            task_id=task_id,
            student_id=student_id,
            content=content,
            links=links if links is not None else [],
        )
        db.session.add(submission)
        db.session.commit()
        return submission.id


def _student_with_course(client, app, enrolled=True, course_active=True, **task_kwargs):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app, active=course_active)
    if enrolled:
        _seed_enrollment(app, course_id, student_id)
    task_id = _seed_task(app, course_id, **task_kwargs)
    _login(client, STUDENT)
    return student_id, course_id, task_id


def _url(course_id, task_id):
    return f"/api/courses/{course_id}/tasks/{task_id}/submission"


def test_submissions_require_session(client, app):
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 401
    assert client.put(_url(course_id, task_id), json={"content": "x"}).status_code == 401
    assert client.delete(_url(course_id, task_id)).status_code == 401


def test_submissions_forbidden_for_teacher(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, TEACHER)
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 403
    assert client.put(_url(course_id, task_id), json={"content": "x"}).status_code == 403
    assert client.delete(_url(course_id, task_id)).status_code == 403


def test_submissions_forbidden_for_admin(client, app):
    _create_user(app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, ADMIN)
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 403


def test_create_submission_course_not_found(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT)
    _login(client, STUDENT)
    assert (
        client.post("/api/courses/9999/tasks/1/submission", json={"content": "x"}).status_code
        == 404
    )


def test_create_submission_without_active_enrollment(client, app):
    _, course_id, task_id = _student_with_course(client, app, enrolled=False)
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 403


def test_create_submission_inactive_enrollment(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id, active=False)
    task_id = _seed_task(app, course_id)
    _login(client, STUDENT)
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 403


def test_create_submission_task_not_found(client, app):
    _, course_id, _ = _student_with_course(client, app)
    assert (
        client.post(
            f"/api/courses/{course_id}/tasks/9999/submission", json={"content": "x"}
        ).status_code
        == 404
    )


def test_create_submission_task_from_other_course(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app, code="PROG1")
    other_course = _seed_course(app, code="PROG2")
    _seed_enrollment(app, course_id, student_id)
    _seed_enrollment(app, other_course, student_id)
    other_task = _seed_task(app, other_course, title="De otro curso")
    _login(client, STUDENT)
    assert client.post(_url(course_id, other_task), json={"content": "x"}).status_code == 404


def test_create_submission_success(client, app):
    _, course_id, task_id = _student_with_course(client, app)
    response = client.post(_url(course_id, task_id), json={"content": "Mi respuesta"})
    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == SUBMISSION_FIELDS
    assert body["task_id"] == task_id
    assert body["content"] == "Mi respuesta"
    assert body["links"] == []


def test_create_submission_with_links_only(client, app):
    _, course_id, task_id = _student_with_course(client, app)
    response = client.post(
        _url(course_id, task_id),
        json={"content": "  ", "links": ["https://example.com", "  "]},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["content"] == ""
    assert body["links"] == ["https://example.com"]


def test_create_submission_requires_content_or_link(client, app):
    _, course_id, task_id = _student_with_course(client, app)
    assert (
        client.post(_url(course_id, task_id), json={"content": "", "links": []}).status_code == 400
    )
    assert client.post(_url(course_id, task_id), json={}).status_code == 400


def test_create_submission_rejects_invalid_links(client, app):
    _, course_id, task_id = _student_with_course(client, app)
    response = client.post(_url(course_id, task_id), json={"links": "no-es-lista"})
    assert response.status_code == 400


def test_create_submission_duplicate(client, app):
    student_id, course_id, task_id = _student_with_course(client, app)
    _seed_submission(app, task_id, student_id, content="Primera")
    response = client.post(_url(course_id, task_id), json={"content": "Segunda"})
    assert response.status_code == 409


def test_create_submission_task_inactive(client, app):
    _, course_id, task_id = _student_with_course(client, app, active=False)
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 409


def test_create_submission_past_due_date(client, app):
    _, course_id, task_id = _student_with_course(
        client, app, due_date=datetime(2020, 1, 1, tzinfo=UTC)
    )
    assert client.post(_url(course_id, task_id), json={"content": "x"}).status_code == 409


def test_update_submission_success(client, app):
    student_id, course_id, task_id = _student_with_course(client, app)
    _seed_submission(app, task_id, student_id, content="Original")
    response = client.put(_url(course_id, task_id), json={"content": "Corregida"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["content"] == "Corregida"


def test_update_submission_not_found(client, app):
    _, course_id, task_id = _student_with_course(client, app)
    assert client.put(_url(course_id, task_id), json={"content": "x"}).status_code == 404


def test_update_submission_validation_error(client, app):
    student_id, course_id, task_id = _student_with_course(client, app)
    _seed_submission(app, task_id, student_id)
    assert client.put(_url(course_id, task_id), json={"content": ""}).status_code == 400


def test_delete_submission_success(client, app):
    student_id, course_id, task_id = _student_with_course(client, app)
    _seed_submission(app, task_id, student_id)
    assert client.delete(_url(course_id, task_id)).status_code == 200
    listing = client.get(f"/api/courses/{course_id}/tasks").get_json()
    assert listing[0]["submission"] is None


def test_delete_submission_not_found(client, app):
    _, course_id, task_id = _student_with_course(client, app)
    assert client.delete(_url(course_id, task_id)).status_code == 404


def test_delete_submission_past_due_date(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id)
    task_id = _seed_task(app, course_id, due_date=datetime(2020, 1, 1, tzinfo=UTC))
    _seed_submission(app, task_id, student_id)
    _login(client, STUDENT)
    assert client.delete(_url(course_id, task_id)).status_code == 409


def test_student_lists_only_available_tasks_with_own_submission(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id)
    available = _seed_task(app, course_id, title="Disponible")
    other_student = _create_user(app, STUDENT_TWO, UserRole.STUDENT)
    _seed_enrollment(app, course_id, other_student)
    _seed_submission(app, available, other_student, content="De otro")
    _seed_task(app, course_id, title="Inactiva", active=False)
    _seed_task(app, course_id, title="Vencida", due_date=datetime(2020, 1, 1, tzinfo=UTC))
    _login(client, STUDENT)

    response = client.get(f"/api/courses/{course_id}/tasks")
    assert response.status_code == 200
    body = response.get_json()
    assert [task["id"] for task in body] == [available]
    assert set(body[0]) == STUDENT_TASK_FIELDS
    assert body[0]["submission"] is None


def test_student_listing_shows_own_submission(client, app):
    student_id, course_id, task_id = _student_with_course(client, app)
    _seed_submission(app, task_id, student_id, content="Mía")
    response = client.get(f"/api/courses/{course_id}/tasks")
    assert response.status_code == 200
    submission = response.get_json()[0]["submission"]
    assert submission is not None
    assert submission["content"] == "Mía"


def test_student_listing_without_enrollment(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_task(app, course_id)
    _login(client, STUDENT)
    assert client.get(f"/api/courses/{course_id}/tasks").status_code == 403


def test_student_listing_course_not_found(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT)
    _login(client, STUDENT)
    assert client.get("/api/courses/9999/tasks").status_code == 404


def test_teacher_listing_still_unrestricted(client, app):
    from models.course_teacher import CourseTeacher

    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    with app.app_context():
        db.session.add(CourseTeacher(course_id=course_id, teacher_id=teacher_id))
        db.session.commit()
    _seed_task(app, course_id, title="Activa")
    _seed_task(app, course_id, title="Inactiva", active=False)
    _seed_task(app, course_id, title="Vencida", due_date=datetime(2020, 1, 1, tzinfo=UTC))
    _login(client, TEACHER)

    response = client.get(f"/api/courses/{course_id}/tasks")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 3
    assert "submission" not in body[0]
