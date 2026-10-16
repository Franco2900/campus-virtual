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

STUDENT_TASK_FIELDS = {
    "task_id",
    "title",
    "due_date",
    "active",
    "submitted",
    "grade",
    "feedback",
    "graded_at",
    "approved",
    "counted",
    "effective_value",
}
STUDENT_VIEW_FIELDS = {"course", "average", "tasks"}
TEACHER_VIEW_FIELDS = {"course", "tasks", "students", "course_average"}
TEACHER_TASK_FIELDS = {"task_id", "title", "due_date", "active"}
STUDENT_ROW_FIELDS = {"student", "grades", "average", "approved"}
STUDENT_INFO_FIELDS = {"id", "name", "email"}
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


def _grades_url(course_id):
    return f"/api/courses/{course_id}/grades"


def _teacher_with_course(client, app, code="PROG1"):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, code=code)
    _assign_teacher(app, course_id, teacher_id)
    _login(client, TEACHER)
    return teacher_id, course_id


def _student_with_course(client, app, credentials=None, code="PROG1"):
    credentials = credentials or STUDENT
    student_id = _create_user(app, credentials, UserRole.STUDENT)
    course_id = _seed_course(app, code=code)
    _seed_enrollment(app, course_id, student_id)
    _login(client, credentials)
    return student_id, course_id


def test_grades_requires_session(client, app):
    course_id = _seed_course(app)
    assert client.get(_grades_url(course_id)).status_code == 401


def test_grades_forbidden_for_admin(client, app):
    _create_user(app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    _login(client, ADMIN)
    assert client.get(_grades_url(course_id)).status_code == 403


def test_grades_course_not_found_for_student(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT)
    _login(client, STUDENT)
    assert client.get(_grades_url(9999)).status_code == 404


def test_grades_course_not_found_for_teacher(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    _login(client, TEACHER)
    assert client.get(_grades_url(9999)).status_code == 404


def test_student_without_active_enrollment_is_forbidden(client, app):
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    _seed_enrollment(app, course_id, student_id, active=False)
    _login(client, STUDENT)
    assert client.get(_grades_url(course_id)).status_code == 403


def test_teacher_not_assigned_is_forbidden(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _login(client, TEACHER)
    assert client.get(_grades_url(course_id)).status_code == 403


def test_student_view_detail_and_average(client, app):
    student_id, course_id = _student_with_course(client, app)
    task_graded = _seed_task(app, course_id, title="Corregida")
    task_expired = _seed_task(app, course_id, title="Vencida", due_date=PAST_DUE_DATE)
    task_pending = _seed_task(app, course_id, title="Sin corregir")
    _seed_submission(
        app,
        task_graded,
        student_id,
        grade=8,
        feedback="Bien",
        graded_at=datetime.now(UTC),
    )
    _seed_submission(app, task_pending, student_id, content="Pendiente")

    response = client.get(_grades_url(course_id))
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == STUDENT_VIEW_FIELDS
    assert body["average"] == 4.5
    assert [task["task_id"] for task in body["tasks"]] == [
        task_graded,
        task_expired,
        task_pending,
    ]

    by_id = {task["task_id"]: task for task in body["tasks"]}
    assert set(by_id[task_graded]) == STUDENT_TASK_FIELDS

    graded = by_id[task_graded]
    assert graded["title"] == "Corregida"
    assert graded["active"] is True
    assert graded["submitted"] is True
    assert graded["grade"] == 8
    assert graded["feedback"] == "Bien"
    assert graded["graded_at"] is not None
    assert graded["approved"] is True
    assert graded["counted"] is True
    assert graded["effective_value"] == 8

    expired = by_id[task_expired]
    assert expired["submitted"] is False
    assert expired["grade"] is None
    assert expired["feedback"] is None
    assert expired["graded_at"] is None
    assert expired["approved"] is False
    assert expired["counted"] is True
    assert expired["effective_value"] == 1

    pending = by_id[task_pending]
    assert pending["submitted"] is True
    assert pending["grade"] is None
    assert pending["approved"] is False
    assert pending["counted"] is False
    assert pending["effective_value"] is None


def test_student_view_is_isolated_from_other_students(client, app):
    student_id, course_id = _student_with_course(client, app)
    other_student_id = _create_user(app, STUDENT_TWO, UserRole.STUDENT)
    _seed_enrollment(app, course_id, other_student_id)
    task_id = _seed_task(app, course_id)
    _seed_submission(app, task_id, student_id, grade=3, graded_at=datetime.now(UTC))
    _seed_submission(app, task_id, other_student_id, grade=9, graded_at=datetime.now(UTC))

    response = client.get(_grades_url(course_id))
    assert response.status_code == 200
    body = response.get_json()
    assert body["average"] == 3
    assert body["tasks"][0]["grade"] == 3
    assert body["tasks"][0]["effective_value"] == 3


def test_student_view_approved_false_below_threshold(client, app):
    student_id, course_id = _student_with_course(client, app)
    task_id = _seed_task(app, course_id)
    _seed_submission(app, task_id, student_id, grade=5, graded_at=datetime.now(UTC))

    body = client.get(_grades_url(course_id)).get_json()
    assert body["tasks"][0]["approved"] is False
    assert body["average"] == 5


def test_student_view_excludes_inactive_not_corrected_and_not_due(client, app):
    student_id, course_id = _student_with_course(client, app)
    inactive_task = _seed_task(app, course_id, title="Inactiva", active=False)
    _seed_submission(app, inactive_task, student_id, grade=10, graded_at=datetime.now(UTC))
    pending_task = _seed_task(app, course_id, title="Sin corregir")
    _seed_submission(app, pending_task, student_id, content="Pendiente")
    not_due_task = _seed_task(app, course_id, title="No vencida")

    body = client.get(_grades_url(course_id)).get_json()
    assert body["average"] is None
    assert [task["task_id"] for task in body["tasks"]] == [pending_task, not_due_task]
    for task in body["tasks"]:
        assert task["counted"] is False
        assert task["effective_value"] is None
        assert task["grade"] is None


def test_teacher_view_matrix(client, app):
    teacher_id, course_id = _teacher_with_course(client, app)
    task_one = _seed_task(app, course_id, title="T1")
    task_two = _seed_task(app, course_id, title="T2", due_date=PAST_DUE_DATE)
    _seed_task(app, course_id, title="Inactiva", active=False)

    student_one = _create_user(app, STUDENT, UserRole.STUDENT, first_name="Ana", last_name="Díaz")
    student_two = _create_user(
        app, STUDENT_TWO, UserRole.STUDENT, first_name="Beto", last_name="Gómez"
    )
    _seed_enrollment(app, course_id, student_one)
    _seed_enrollment(app, course_id, student_two)
    inactive_student = _create_user(
        app, {"email": "student3@example.com", "password": "student3pass123"}, UserRole.STUDENT
    )
    _seed_enrollment(app, course_id, inactive_student, active=False)

    _seed_submission(app, task_one, student_one, grade=8, graded_at=datetime.now(UTC))

    response = client.get(_grades_url(course_id))
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == TEACHER_VIEW_FIELDS
    assert [task["task_id"] for task in body["tasks"]] == [task_one, task_two]
    assert all(set(task) == TEACHER_TASK_FIELDS for task in body["tasks"])

    assert len(body["students"]) == 2
    rows = {row["student"]["id"]: row for row in body["students"]}
    assert set(rows) == {student_one, student_two}
    assert set(rows[student_one]) == STUDENT_ROW_FIELDS
    assert set(rows[student_one]["student"]) == STUDENT_INFO_FIELDS
    assert rows[student_one]["student"]["name"] == "Ana Díaz"
    assert rows[student_one]["student"]["email"] == STUDENT["email"]

    assert rows[student_one]["grades"] == {str(task_one): 8, str(task_two): 1}
    assert rows[student_one]["average"] == 4.5
    assert rows[student_two]["grades"] == {str(task_one): None, str(task_two): 1}
    assert rows[student_two]["average"] == 1
    assert rows[student_one]["approved"] is False
    assert rows[student_two]["approved"] is False
    assert body["course_average"] == 2.75
    assert teacher_id > 0


def test_teacher_view_student_approval_state(client, app):
    _, course_id = _teacher_with_course(client, app)
    task = _seed_task(app, course_id, title="T1")

    approved_student = _create_user(
        app, STUDENT, UserRole.STUDENT, first_name="Apro", last_name="Bado"
    )
    boundary_student = _create_user(
        app,
        {"email": "boundary@example.com", "password": "boundarypass123"},
        UserRole.STUDENT,
        first_name="Justo",
        last_name="Seis",
    )
    failed_student = _create_user(
        app, STUDENT_TWO, UserRole.STUDENT, first_name="Desa", last_name="Probado"
    )
    _seed_enrollment(app, course_id, approved_student)
    _seed_enrollment(app, course_id, boundary_student)
    _seed_enrollment(app, course_id, failed_student)

    _seed_submission(app, task, approved_student, grade=8, graded_at=datetime.now(UTC))
    _seed_submission(app, task, boundary_student, grade=6, graded_at=datetime.now(UTC))
    _seed_submission(app, task, failed_student, grade=5, graded_at=datetime.now(UTC))

    response = client.get(_grades_url(course_id))
    assert response.status_code == 200
    rows = {row["student"]["id"]: row for row in response.get_json()["students"]}
    assert rows[approved_student]["average"] == 8
    assert rows[approved_student]["approved"] is True
    assert rows[boundary_student]["average"] == 6
    assert rows[boundary_student]["approved"] is True
    assert rows[failed_student]["average"] == 5
    assert rows[failed_student]["approved"] is False


def test_teacher_view_without_students(client, app):
    _, course_id = _teacher_with_course(client, app)
    _seed_task(app, course_id)

    response = client.get(_grades_url(course_id))
    assert response.status_code == 200
    body = response.get_json()
    assert body["students"] == []
    assert body["course_average"] is None
    assert len(body["tasks"]) == 1


def test_teacher_view_without_active_tasks(client, app):
    _, course_id = _teacher_with_course(client, app)
    _seed_task(app, course_id, title="Inactiva", active=False)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    _seed_enrollment(app, course_id, student_id)

    response = client.get(_grades_url(course_id))
    assert response.status_code == 200
    body = response.get_json()
    assert body["tasks"] == []
    assert body["course_average"] is None
    assert len(body["students"]) == 1
    assert body["students"][0]["grades"] == {}
    assert body["students"][0]["average"] is None
    assert body["students"][0]["approved"] is False
