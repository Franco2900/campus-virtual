import pytest
from werkzeug.security import generate_password_hash

from models.base import db
from models.course import Course
from models.user import User, UserRole
from services import course_service
from services.errors import ConflictError, NotFoundError, ValidationError

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}
COURSE = {"name": "Programación I", "code": "PROG1", "description": "Introducción"}


def _create_user(app, credentials, role):
    with app.app_context():
        user = User(
            first_name="Nombre",
            last_name="Apellido",
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


def _seed_course(app, code="PROG1", name="Programación I", active=True):
    with app.app_context():
        course = Course(name=name, code=code, description="", active=active)
        db.session.add(course)
        db.session.commit()
        return course.id


def test_list_courses_requires_session(client):
    response = client.get("/api/courses")
    assert response.status_code == 401


def test_list_courses_forbidden_for_student(client, app):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    response = client.get("/api/courses")
    assert response.status_code == 403


def test_list_courses_forbidden_for_teacher(client, app):
    _login_as(client, app, TEACHER, UserRole.TEACHER)
    response = client.get("/api/courses")
    assert response.status_code == 403


def test_create_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.post("/api/courses", json=COURSE)
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Programación I"
    assert body["code"] == "PROG1"
    assert body["active"] is True
    assert set(body) == {"id", "name", "code", "description", "active", "created_at"}


def test_create_course_missing_fields(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.post("/api/courses", json={"description": "sin nombre ni código"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_course_duplicate_code_case_insensitive(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    client.post("/api/courses", json=COURSE)
    response = client.post("/api/courses", json={"name": "Otra", "code": "prog1"})
    assert response.status_code == 409


def test_list_courses_includes_inactive(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    _seed_course(app, code="ACT1", active=True)
    _seed_course(app, code="INA1", active=False)
    response = client.get("/api/courses")
    assert response.status_code == 200
    codes = {course["code"] for course in response.get_json()}
    assert codes == {"ACT1", "INA1"}


def test_get_course_not_found(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.get("/api/courses/999")
    assert response.status_code == 404


def test_update_course(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    response = client.put(
        f"/api/courses/{course_id}", json={"name": "Programación II", "code": "PROG2"}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "Programación II"
    assert body["code"] == "PROG2"


def test_update_course_not_found(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.put("/api/courses/999", json={"name": "X", "code": "X1"})
    assert response.status_code == 404


def test_update_course_duplicate_code(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    _seed_course(app, code="PROG1")
    other_id = _seed_course(app, code="PROG2", name="Programación II")
    response = client.put(f"/api/courses/{other_id}", json={"name": "X", "code": "prog1"})
    assert response.status_code == 409


def test_patch_deactivate_and_reactivate(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app, active=True)

    deactivate = client.patch(f"/api/courses/{course_id}", json={"active": False})
    assert deactivate.status_code == 200
    assert deactivate.get_json()["active"] is False

    reactivate = client.patch(f"/api/courses/{course_id}", json={"active": True})
    assert reactivate.status_code == 200
    assert reactivate.get_json()["active"] is True


def test_patch_invalid_body(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    response = client.patch(f"/api/courses/{course_id}", json={"active": "no"})
    assert response.status_code == 400


def test_patch_course_not_found(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.patch("/api/courses/999", json={"active": False})
    assert response.status_code == 404


def test_service_create_normalizes_code(app):
    with app.app_context():
        course = course_service.create_course(
            {"name": "Física", "code": " fis1 ", "description": ""}
        )
        assert course.code == "FIS1"
        assert course.active is True


def test_service_create_duplicate_raises_conflict(app):
    with app.app_context():
        course_service.create_course({"name": "Física", "code": "FIS1"})
        with pytest.raises(ConflictError):
            course_service.create_course({"name": "Otra", "code": "fis1"})


def test_service_create_missing_fields_raises_validation(app):
    with app.app_context(), pytest.raises(ValidationError):
        course_service.create_course({"name": "", "code": "X1"})


def test_service_get_missing_raises_not_found(app):
    with app.app_context(), pytest.raises(NotFoundError):
        course_service.get_course_or_404(12345)
