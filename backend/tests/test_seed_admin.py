import pytest
from scripts.seed_admin import (
    SeedError,
    provision_admin,
    read_credentials,
    seed_demo_courses,
)

from models.base import db
from models.course import Course
from models.user import User

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpass123"


def test_read_credentials_missing_env_raises():
    with pytest.raises(SeedError):
        read_credentials({})
    with pytest.raises(SeedError):
        read_credentials({"CAMPUS_ADMIN_EMAIL": ADMIN_EMAIL})


def test_provision_admin_creates_admin_that_can_login(app, client):
    assert provision_admin(app, ADMIN_EMAIL, ADMIN_PASSWORD) is True
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    assert response.get_json()["role"] == "admin"


def test_provision_admin_is_idempotent(app):
    assert provision_admin(app, ADMIN_EMAIL, ADMIN_PASSWORD) is True
    assert provision_admin(app, ADMIN_EMAIL, "otraClave123") is False
    with app.app_context():
        users = db.session.execute(db.select(User).where(User.email == ADMIN_EMAIL)).scalars().all()
        assert len(users) == 1


def test_seed_demo_courses_creates_four(app):
    assert seed_demo_courses(app) == 4
    with app.app_context():
        courses = db.session.execute(db.select(Course)).scalars().all()
        assert len(courses) == 4
        assert any(course.active for course in courses)
        assert any(not course.active for course in courses)


def test_seed_demo_courses_is_idempotent(app):
    seed_demo_courses(app)
    assert seed_demo_courses(app) == 0
    with app.app_context():
        courses = db.session.execute(db.select(Course)).scalars().all()
        assert len(courses) == 4
