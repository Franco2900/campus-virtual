from werkzeug.security import generate_password_hash

from models.base import db
from models.course import Course
from models.user import User, UserRole

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}


def _create_user(app, credentials, role, first_name="Nombre", last_name="Apellido"):
    with app.app_context():
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=credentials["email"].lower(),
            password_hash=generate_password_hash(credentials["password"]),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login_as(client, app, credentials, role):
    _create_user(app, credentials, role)
    return client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )


def _seed_course(app, code="PROG1"):
    with app.app_context():
        course = Course(name="Programación I", code=code, description="", active=True)
        db.session.add(course)
        db.session.commit()
        return course.id


def test_list_teachers_requires_session(client, app):
    course_id = _seed_course(app)
    response = client.get(f"/api/courses/{course_id}/teachers")
    assert response.status_code == 401


def test_list_teachers_forbidden_for_student(client, app):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    response = client.get(f"/api/courses/{course_id}/teachers")
    assert response.status_code == 403


def test_assign_teacher_success(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    response = client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": teacher_id})
    assert response.status_code == 201
    assert response.get_json()["role"] == "teacher"


def test_assign_teacher_rejects_non_teacher(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": student_id})
    assert response.status_code == 400


def test_assign_teacher_duplicate(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": teacher_id})
    response = client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": teacher_id})
    assert response.status_code == 409


def test_assign_teacher_missing_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    response = client.post("/api/courses/9999/teachers", json={"teacher_id": teacher_id})
    assert response.status_code == 404


def test_assign_teacher_missing_user(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    response = client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": 9999})
    assert response.status_code == 404


def test_assign_teacher_missing_payload(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    response = client.post(f"/api/courses/{course_id}/teachers", json={})
    assert response.status_code == 400


def test_list_teachers_returns_assigned(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": teacher_id})
    response = client.get(f"/api/courses/{course_id}/teachers")
    assert response.status_code == 200
    body = response.get_json()
    assert [teacher["id"] for teacher in body] == [teacher_id]
    assert "password_hash" not in body[0]


def test_list_teachers_missing_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.get("/api/courses/9999/teachers")
    assert response.status_code == 404


def test_remove_teacher_success(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    client.post(f"/api/courses/{course_id}/teachers", json={"teacher_id": teacher_id})

    removed = client.delete(f"/api/courses/{course_id}/teachers/{teacher_id}")
    assert removed.status_code == 200

    listed = client.get(f"/api/courses/{course_id}/teachers")
    assert listed.get_json() == []


def test_remove_teacher_missing_assignment(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    response = client.delete(f"/api/courses/{course_id}/teachers/{teacher_id}")
    assert response.status_code == 404


def test_remove_teacher_missing_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.delete("/api/courses/9999/teachers/1")
    assert response.status_code == 404
