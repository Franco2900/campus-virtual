from werkzeug.security import generate_password_hash

from models.base import db
from models.user import User, UserRole


VALID_USER = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "password": "strongpass123",
}


def _create_user(app, email=VALID_USER["email"], password=VALID_USER["password"], role=UserRole.STUDENT):
    with app.app_context():
        user = User(
            first_name=VALID_USER["first_name"],
            last_name=VALID_USER["last_name"],
            email=email.lower(),
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def test_login_success(client, app):
    _create_user(app)
    response = client.post(
        "/api/auth/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"id", "first_name", "last_name", "email", "role"}
    assert body["email"] == "ada@example.com"
    assert body["role"] == "student"
    assert "password" not in body
    assert "password_hash" not in body


def test_login_without_email(client):
    response = client.post("/api/auth/login", json={"password": VALID_USER["password"]})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_login_without_password(client):
    response = client.post("/api/auth/login", json={"email": VALID_USER["email"]})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_login_unknown_email_returns_generic_401(client, app):
    _create_user(app)
    response = client.post(
        "/api/auth/login", json={"email": "unknown@example.com", "password": VALID_USER["password"]}
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "El correo electrónico o la contraseña son incorrectos"


def test_login_wrong_password_returns_generic_401(client, app):
    _create_user(app)
    response = client.post(
        "/api/auth/login", json={"email": VALID_USER["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    body = response.get_json()
    assert body["error"] == "El correo electrónico o la contraseña son incorrectos"


def test_me_without_session(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_session(client, app):
    _create_user(app)
    client.post("/api/auth/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    body = response.get_json()
    assert body["role"] == "student"
    assert set(body) == {"id", "first_name", "last_name", "email", "role"}


def test_session_persists_between_requests(client, app):
    _create_user(app)
    login_response = client.post(
        "/api/auth/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]}
    )
    assert login_response.status_code == 200
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.get_json()["email"] == "ada@example.com"


def test_logout_with_session(client, app):
    _create_user(app)
    client.post("/api/auth/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]})
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.get_json()["message"] == "Sesión cerrada"
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_logout_without_session(client):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Sesión cerrada"


def test_login_sets_httponly_cookie(client, app):
    _create_user(app)
    response = client.post(
        "/api/auth/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]}
    )
    assert response.status_code == 200
    cookie_header = response.headers.get("Set-Cookie", "")
    assert "session" in cookie_header
    assert "HttpOnly" in cookie_header
