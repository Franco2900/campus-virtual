from werkzeug.security import generate_password_hash

from models.base import db
from models.user import User, UserRole

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}


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


def _login_as(client, app, credentials, role):
    _create_user(app, credentials, role)
    return client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )


def test_list_users_requires_session(client):
    response = client.get("/api/users")
    assert response.status_code == 401


def test_list_users_forbidden_for_student(client, app):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    response = client.get("/api/users")
    assert response.status_code == 403


def test_list_users_forbidden_for_teacher(client, app):
    _login_as(client, app, TEACHER, UserRole.TEACHER)
    response = client.get("/api/users")
    assert response.status_code == 403


def test_list_users_includes_inactive_and_hides_password(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    _create_user(app, STUDENT, UserRole.STUDENT, active=False)
    response = client.get("/api/users")
    assert response.status_code == 200
    body = response.get_json()
    emails = {user["email"] for user in body}
    assert STUDENT["email"] in emails
    for user in body:
        assert "password_hash" not in user
        assert "password" not in user
    inactive = next(user for user in body if user["email"] == STUDENT["email"])
    assert inactive["active"] is False


def test_get_user_success(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.get(f"/api/users/{student_id}")
    assert response.status_code == 200
    assert response.get_json()["email"] == STUDENT["email"]


def test_get_user_missing(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.get("/api/users/9999")
    assert response.status_code == 404


def test_update_user_success(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.put(
        f"/api/users/{student_id}",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada.nueva@example.com",
            "role": "student",
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["first_name"] == "Ada"
    assert body["email"] == "ada.nueva@example.com"


def test_update_user_role_student_to_teacher(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.put(
        f"/api/users/{student_id}",
        json={
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": STUDENT["email"],
            "role": "teacher",
        },
    )
    assert response.status_code == 200
    assert response.get_json()["role"] == "teacher"


def test_update_user_email_conflict(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    _create_user(app, STUDENT, UserRole.STUDENT)
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    response = client.put(
        f"/api/users/{teacher_id}",
        json={
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": STUDENT["email"],
            "role": "teacher",
        },
    )
    assert response.status_code == 409


def test_update_user_invalid_role(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.put(
        f"/api/users/{student_id}",
        json={
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": STUDENT["email"],
            "role": "wizard",
        },
    )
    assert response.status_code == 400


def test_update_user_missing_fields(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.put(
        f"/api/users/{student_id}",
        json={
            "first_name": "",
            "last_name": "Apellido",
            "email": STUDENT["email"],
            "role": "student",
        },
    )
    assert response.status_code == 400


def test_update_user_missing_user(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.put(
        "/api/users/9999",
        json={
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "x@example.com",
            "role": "student",
        },
    )
    assert response.status_code == 404


def test_patch_user_deactivate_and_reactivate(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)

    deactivate = client.patch(f"/api/users/{student_id}", json={"active": False})
    assert deactivate.status_code == 200
    assert deactivate.get_json()["active"] is False

    reactivate = client.patch(f"/api/users/{student_id}", json={"active": True})
    assert reactivate.status_code == 200
    assert reactivate.get_json()["active"] is True


def test_patch_user_missing_active_flag(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.patch(f"/api/users/{student_id}", json={})
    assert response.status_code == 400


def test_patch_user_missing_user(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    response = client.patch("/api/users/9999", json={"active": False})
    assert response.status_code == 404


def test_admin_cannot_deactivate_self(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    with app.app_context():
        admin = db.session.execute(db.select(User).where(User.email == ADMIN["email"])).scalar_one()
        admin_id = admin.id
    response = client.patch(f"/api/users/{admin_id}", json={"active": False})
    assert response.status_code == 400


def test_admin_cannot_change_own_role(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    with app.app_context():
        admin = db.session.execute(db.select(User).where(User.email == ADMIN["email"])).scalar_one()
        admin_id = admin.id
    response = client.put(
        f"/api/users/{admin_id}",
        json={
            "first_name": "Admin",
            "last_name": "Root",
            "email": ADMIN["email"],
            "role": "student",
        },
    )
    assert response.status_code == 400


def test_reset_password_success_allows_login(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.post(f"/api/users/{student_id}/password", json={"password": "newstrongpass1"})
    assert response.status_code == 200

    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login", json={"email": STUDENT["email"], "password": "newstrongpass1"}
    )
    assert login.status_code == 200


def test_reset_password_too_short(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    student_id = _create_user(app, STUDENT, UserRole.STUDENT)
    response = client.post(f"/api/users/{student_id}/password", json={"password": "short"})
    assert response.status_code == 400


def test_inactive_user_cannot_login(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT, active=False)
    response = client.post(
        "/api/auth/login", json={"email": STUDENT["email"], "password": STUDENT["password"]}
    )
    assert response.status_code == 401


def test_inactive_session_is_rejected(client, app):
    _create_user(app, STUDENT, UserRole.STUDENT)
    login = client.post(
        "/api/auth/login", json={"email": STUDENT["email"], "password": STUDENT["password"]}
    )
    assert login.status_code == 200

    with app.app_context():
        student = db.session.execute(
            db.select(User).where(User.email == STUDENT["email"])
        ).scalar_one()
        student.active = False
        db.session.commit()

    me = client.get("/api/auth/me")
    assert me.status_code == 401
