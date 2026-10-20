import io

import pytest
from werkzeug.security import generate_password_hash

from models.base import db
from models.user import User, UserRole
from services import knowledge_service
from services.knowledge_service import KnowledgeServiceError

SOURCES_URL = "/api/knowledge/sources"

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}


def _create_user(app, credentials, role):
    with app.app_context():
        user = User(
            first_name="Nombre",
            last_name="Apellido",
            email=credentials["email"].lower(),
            password_hash=generate_password_hash(credentials["password"]),
            role=role,
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, credentials):
    return client.post(
        "/api/auth/login",
        json={"email": credentials["email"], "password": credentials["password"]},
    )


def _login_as(client, app, credentials, role):
    _create_user(app, credentials, role)
    return _login(client, credentials)


def _fake_source_row(source_id=1):
    from models.knowledge_source import KnowledgeSource, KnowledgeSourceStatus, KnowledgeSourceType

    return KnowledgeSource(
        id=source_id,
        name="Guía",
        description="Propósito",
        source_type=KnowledgeSourceType.DOCUMENT,
        status=KnowledgeSourceStatus.ACTIVE,
        target_roles=["student"],
        original_filename="guia.md",
        stored_filename="abc.md",
        file_size_bytes=120,
        chunk_count=3,
    )


def test_list_sources_without_session_returns_401(client):
    response = client.get(SOURCES_URL)
    assert response.status_code == 401
    assert "error" in response.get_json()


def test_create_source_without_session_returns_401(client):
    response = client.post(SOURCES_URL, data={})
    assert response.status_code == 401


def test_delete_source_without_session_returns_401(client):
    response = client.delete(f"{SOURCES_URL}/1")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", SOURCES_URL),
        ("delete", f"{SOURCES_URL}/1"),
    ],
)
def test_non_admin_is_forbidden(client, app, method, url):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    response = getattr(client, method)(url)
    assert response.status_code == 403
    assert "permisos" in response.get_json()["error"]


def test_non_admin_cannot_create(client, app):
    _login_as(client, app, TEACHER, UserRole.TEACHER)
    response = client.post(SOURCES_URL, data={})
    assert response.status_code == 403


def test_list_sources_returns_metadata(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    monkeypatch.setattr(
        knowledge_service, "list_sources", lambda: [_fake_source_row(1), _fake_source_row(2)]
    )

    response = client.get(SOURCES_URL)

    assert response.status_code == 200
    body = response.get_json()
    assert [row["id"] for row in body["sources"]] == [1, 2]
    row = body["sources"][0]
    for key in (
        "id",
        "name",
        "description",
        "source_type",
        "status",
        "target_roles",
        "original_filename",
        "file_size_bytes",
        "chunk_count",
        "error_message",
        "created_at",
        "updated_at",
    ):
        assert key in row


def test_create_source_returns_201(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)

    def fake_create(file_storage, form_data, current_user=None):
        return _fake_source_row(7)

    monkeypatch.setattr(knowledge_service, "create_source", fake_create)

    response = client.post(
        SOURCES_URL,
        data={
            "file": (io.BytesIO(b"contenido"), "guia.md"),
            "name": "Guía",
            "source_type": "document",
            "target_roles": "student",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    body = response.get_json()
    assert "message" in body
    assert body["source"]["id"] == 7


def test_create_source_validation_error_returns_400(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)

    def fake_create(file_storage, form_data, current_user=None):
        raise knowledge_service.ValidationError("El formato del archivo no está admitido")

    monkeypatch.setattr(knowledge_service, "create_source", fake_create)

    response = client.post(
        SOURCES_URL,
        data={"file": (io.BytesIO(b"x"), "guia.pdf"), "name": "Guía", "source_type": "document"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_source_processing_error_returns_400(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)

    def fake_create(file_storage, form_data, current_user=None):
        raise KnowledgeServiceError("No se pudo procesar la fuente")

    monkeypatch.setattr(knowledge_service, "create_source", fake_create)

    response = client.post(
        SOURCES_URL,
        data={"file": (io.BytesIO(b"x"), "guia.md"), "name": "Guía", "source_type": "document"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "No se pudo procesar" in response.get_json()["error"]


def test_delete_source_returns_200(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    monkeypatch.setattr(knowledge_service, "delete_source", lambda source_id: None)

    response = client.delete(f"{SOURCES_URL}/3")

    assert response.status_code == 200
    assert "message" in response.get_json()


def test_delete_source_missing_returns_404(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)

    def fake_delete(source_id):
        raise knowledge_service.NotFoundError("Fuente no encontrada")

    monkeypatch.setattr(knowledge_service, "delete_source", fake_delete)

    response = client.delete(f"{SOURCES_URL}/9999")

    assert response.status_code == 404
    assert "error" in response.get_json()


def test_delete_source_service_error_returns_500(client, app, monkeypatch):
    _login_as(client, app, ADMIN, UserRole.ADMIN)

    def fake_delete(source_id):
        raise KnowledgeServiceError("No se pudo eliminar la fuente")

    monkeypatch.setattr(knowledge_service, "delete_source", fake_delete)

    response = client.delete(f"{SOURCES_URL}/3")

    assert response.status_code == 500
    assert "error" in response.get_json()
