import pytest
from werkzeug.security import check_password_hash

from models.base import db
from models.user import User

VALID_PAYLOAD = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "password": "strongpass123",
}


def test_register_success(client):
    response = client.post("/api/auth/register", json=VALID_PAYLOAD)

    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == {"id", "first_name", "last_name", "email", "role"}
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert body["email"] == "ada@example.com"
    assert body["role"] == "student"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json=VALID_PAYLOAD)

    response = client.post("/api/auth/register", json=VALID_PAYLOAD)

    assert response.status_code == 409
    assert "error" in response.get_json()


def test_register_duplicate_email_case_insensitive(client):
    client.post("/api/auth/register", json=VALID_PAYLOAD)

    response = client.post(
        "/api/auth/register", json={**VALID_PAYLOAD, "email": "ADA@Example.COM"}
    )

    assert response.status_code == 409


def test_register_normalizes_email(client):
    response = client.post(
        "/api/auth/register", json={**VALID_PAYLOAD, "email": "Ada@Example.COM"}
    )

    assert response.status_code == 201
    assert response.get_json()["email"] == "ada@example.com"


@pytest.mark.parametrize(
    "email",
    ["not-an-email", "missing@domain", "@example.com", "a b@example.com", "user@"],
)
def test_register_invalid_email(client, email):
    response = client.post("/api/auth/register", json={**VALID_PAYLOAD, "email": email})

    assert response.status_code == 400
    assert "error" in response.get_json()


@pytest.mark.parametrize("field", ["first_name", "last_name", "email", "password"])
def test_register_missing_field(client, field):
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != field}

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400


@pytest.mark.parametrize("field", ["first_name", "last_name", "email", "password"])
def test_register_blank_field(client, field):
    response = client.post(
        "/api/auth/register", json={**VALID_PAYLOAD, field: "   "}
    )

    assert response.status_code == 400


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register", json={**VALID_PAYLOAD, "password": "short"}
    )

    assert response.status_code == 400


def test_register_missing_json_body(client):
    response = client.post(
        "/api/auth/register", data="not json", content_type="application/json"
    )

    assert response.status_code == 400


def test_register_role_is_ignored(client):
    response = client.post(
        "/api/auth/register", json={**VALID_PAYLOAD, "role": "admin"}
    )

    assert response.status_code == 201
    assert response.get_json()["role"] == "student"


def test_password_is_hashed(client, app):
    client.post("/api/auth/register", json=VALID_PAYLOAD)

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == "ada@example.com")
        ).scalar_one()

    assert user.password_hash != VALID_PAYLOAD["password"]
    assert check_password_hash(user.password_hash, VALID_PAYLOAD["password"])
