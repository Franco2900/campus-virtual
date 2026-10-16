from werkzeug.security import generate_password_hash

from models.base import db
from models.user import User, UserRole

PASSWORD = "password123"
ADMIN = {"email": "admin@example.com", "password": PASSWORD}
TEACHER = {"email": "teacher@example.com", "password": PASSWORD}
STUDENT = {"email": "student@example.com", "password": PASSWORD}


def _create_user(
    app,
    *,
    first_name,
    last_name,
    email,
    role,
    active=True,
):
    with app.app_context():
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            password_hash=generate_password_hash(PASSWORD),
            role=role,
            active=active,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, app, credentials, role, first_name="Nombre", last_name="Apellido"):
    _create_user(
        app,
        first_name=first_name,
        last_name=last_name,
        email=credentials["email"],
        role=role,
    )
    return client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )


def _emails(response):
    return {user["email"] for user in response.get_json()}


def test_filter_without_criteria_returns_all_ordered_by_id(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    ana_id = _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    bruno_id = _create_user(
        app,
        first_name="Bruno",
        last_name="Diaz",
        email="bruno@example.com",
        role=UserRole.TEACHER,
        active=False,
    )

    response = client.get("/api/users")

    assert response.status_code == 200
    body = response.get_json()
    assert {"ana@example.com", "bruno@example.com"} <= _emails(response)
    ids = [user["id"] for user in body]
    assert ids == sorted(ids)
    assert {ana_id, bruno_id} <= set(ids)


def test_filter_q_matches_first_name_case_insensitive(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app, first_name="Bruno", last_name="Diaz", email="bruno@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?q=ANA")

    assert response.status_code == 200
    assert _emails(response) == {"ana@example.com"}


def test_filter_q_matches_last_name(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app, first_name="Bruno", last_name="Diaz", email="bruno@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?q=diaz")

    assert response.status_code == 200
    assert _emails(response) == {"bruno@example.com"}


def test_filter_q_matches_email(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app, first_name="Bruno", last_name="Diaz", email="bruno@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?q=bruno@")

    assert response.status_code == 200
    assert _emails(response) == {"bruno@example.com"}


def test_filter_q_blank_is_treated_as_absent(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )

    unfiltered = client.get("/api/users")
    blank = client.get("/api/users?q=%20%20")

    assert blank.status_code == 200
    assert _emails(blank) == _emails(unfiltered)


def test_filter_q_percent_is_literal_not_wildcard(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?q=%25")

    assert response.status_code == 200
    assert response.get_json() == []


def test_filter_q_underscore_is_literal_not_wildcard(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="A_b", last_name="Literal", email="a_b@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app, first_name="Axb", last_name="Other", email="axb@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?q=a_b")

    assert response.status_code == 200
    assert _emails(response) == {"a_b@example.com"}


def test_filter_by_role(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app, first_name="Tomas", last_name="Diaz", email="tomas@example.com", role=UserRole.TEACHER
    )

    students = client.get("/api/users?role=student")
    teachers = client.get("/api/users?role=teacher")

    assert students.status_code == 200
    assert _emails(students) == {"ana@example.com"}
    assert teachers.status_code == 200
    assert _emails(teachers) == {"tomas@example.com"}


def test_filter_by_active(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app,
        first_name="Bruno",
        last_name="Diaz",
        email="bruno@example.com",
        role=UserRole.STUDENT,
        active=False,
    )

    inactive = client.get("/api/users?active=false")
    active = client.get("/api/users?active=true")

    assert inactive.status_code == 200
    assert "bruno@example.com" in _emails(inactive)
    assert "ana@example.com" not in _emails(inactive)
    assert active.status_code == 200
    assert "ana@example.com" in _emails(active)
    assert "bruno@example.com" not in _emails(active)


def test_filter_combined_criteria_use_and(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )
    _create_user(
        app,
        first_name="Ana",
        last_name="Diaz",
        email="ana.diaz@example.com",
        role=UserRole.TEACHER,
    )
    _create_user(
        app,
        first_name="Ana",
        last_name="Ruiz",
        email="ana.ruiz@example.com",
        role=UserRole.STUDENT,
        active=False,
    )

    response = client.get("/api/users?q=ana&role=student&active=true")

    assert response.status_code == 200
    assert _emails(response) == {"ana@example.com"}


def test_filter_invalid_role_returns_400(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?role=superuser")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_filter_invalid_active_returns_400(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")

    response = client.get("/api/users?active=maybe")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_filter_active_without_value_returns_400(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")

    response = client.get("/api/users?active=")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_filter_invalid_role_precedes_valid_criteria(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )

    response = client.get("/api/users?q=ana&role=invalido")

    assert response.status_code == 400


def test_filter_requires_session(client):
    response = client.get("/api/users?q=ana")

    assert response.status_code == 401


def test_filter_forbidden_for_teacher_with_criteria(client, app):
    _login(client, app, TEACHER, UserRole.TEACHER, first_name="Tomas", last_name="Diaz")

    response = client.get("/api/users?role=student")

    assert response.status_code == 403


def test_filter_forbidden_for_teacher_without_criteria(client, app):
    _login(client, app, TEACHER, UserRole.TEACHER, first_name="Tomas", last_name="Diaz")

    response = client.get("/api/users")

    assert response.status_code == 403


def test_filter_forbidden_for_student_with_criteria(client, app):
    _login(client, app, STUDENT, UserRole.STUDENT, first_name="Ana", last_name="Gomez")

    response = client.get("/api/users?q=ana")

    assert response.status_code == 403


def test_filter_does_not_modify_data(client, app):
    _login(client, app, ADMIN, UserRole.ADMIN, first_name="Admin", last_name="Root")
    student_id = _create_user(
        app, first_name="Ana", last_name="Gomez", email="ana@example.com", role=UserRole.STUDENT
    )

    def snapshot():
        with app.app_context():
            user = db.session.get(User, student_id)
            return (
                user.id,
                user.first_name,
                user.last_name,
                user.email,
                user.role,
                user.active,
            )

    before = snapshot()
    response = client.get("/api/users?q=ana&role=student&active=true")
    after = snapshot()

    assert response.status_code == 200
    assert before == after
