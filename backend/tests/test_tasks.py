from datetime import UTC, datetime

from werkzeug.security import generate_password_hash

from models.base import db
from models.course import Course
from models.course_teacher import CourseTeacher
from models.task import Task
from models.user import User, UserRole

ADMIN = {"email": "admin@example.com", "password": "adminpass123"}
STUDENT = {"email": "student@example.com", "password": "studentpass123"}
TEACHER = {"email": "teacher@example.com", "password": "teacherpass123"}

DUE_DATE = "2026-12-01T10:00:00"
DUE_DATE_Z = "2026-12-01T13:00:00Z"
NEW_DUE_DATE = "2027-01-15T08:30:00"
TASK_FIELDS = {"id", "course_id", "title", "description", "due_date", "active"}


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


def _login_as(client, app, credentials, role, **kwargs):
    _create_user(app, credentials, role, **kwargs)
    return _login(client, credentials)


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


def _seed_task(
    app,
    course_id,
    title="Tarea 1",
    description="",
    due_date=datetime(2026, 12, 1, 10, 0, 0, tzinfo=UTC),
    active=True,
):
    with app.app_context():
        task = Task(
            course_id=course_id,
            title=title,
            description=description,
            due_date=due_date,
            active=active,
        )
        db.session.add(task)
        db.session.commit()
        return task.id


def _count_tasks(app, course_id):
    with app.app_context():
        tasks = db.session.execute(db.select(Task).where(Task.course_id == course_id)).scalars()
        return len(tasks.all())


def _teacher_with_course(client, app, course_active=True, assign=True):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, active=course_active)
    if assign:
        _assign_teacher(app, course_id, teacher_id)
    _login(client, TEACHER)
    return teacher_id, course_id


def test_tasks_require_session(client, app):
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    assert client.get(f"/api/courses/{course_id}/tasks").status_code == 401
    assert client.post(f"/api/courses/{course_id}/tasks", json={}).status_code == 401
    assert client.get(f"/api/courses/{course_id}/tasks/{task_id}").status_code == 401
    assert client.put(f"/api/courses/{course_id}/tasks/{task_id}", json={}).status_code == 401
    assert client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={}).status_code == 401


def test_tasks_forbidden_for_student(client, app):
    _login_as(client, app, STUDENT, UserRole.STUDENT)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    assert client.get(f"/api/courses/{course_id}/tasks").status_code == 403
    assert client.post(f"/api/courses/{course_id}/tasks", json={}).status_code == 403
    assert client.get(f"/api/courses/{course_id}/tasks/{task_id}").status_code == 403
    assert client.put(f"/api/courses/{course_id}/tasks/{task_id}", json={}).status_code == 403
    assert client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={}).status_code == 403


def test_tasks_forbidden_for_admin(client, app):
    _login_as(client, app, ADMIN, UserRole.ADMIN)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    assert client.get(f"/api/courses/{course_id}/tasks").status_code == 403
    assert client.post(f"/api/courses/{course_id}/tasks", json={}).status_code == 403
    assert client.get(f"/api/courses/{course_id}/tasks/{task_id}").status_code == 403
    assert client.put(f"/api/courses/{course_id}/tasks/{task_id}", json={}).status_code == 403
    assert client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={}).status_code == 403


def test_tasks_forbidden_for_unassigned_teacher(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    task_id = _seed_task(app, course_id)
    _login(client, TEACHER)
    assert client.get(f"/api/courses/{course_id}/tasks").status_code == 403
    assert client.post(f"/api/courses/{course_id}/tasks", json={"title": "x"}).status_code == 403
    assert client.get(f"/api/courses/{course_id}/tasks/{task_id}").status_code == 403
    assert (
        client.put(
            f"/api/courses/{course_id}/tasks/{task_id}",
            json={"title": "x", "due_date": DUE_DATE},
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/courses/{course_id}/tasks/{task_id}", json={"active": False}
        ).status_code
        == 403
    )


def test_tasks_missing_course(client, app):
    _create_user(app, TEACHER, UserRole.TEACHER)
    _login(client, TEACHER)
    assert client.get("/api/courses/9999/tasks").status_code == 404
    assert (
        client.post(
            "/api/courses/9999/tasks", json={"title": "T", "due_date": DUE_DATE}
        ).status_code
        == 404
    )
    assert client.get("/api/courses/9999/tasks/1").status_code == 404
    assert (
        client.put(
            "/api/courses/9999/tasks/1", json={"title": "T", "due_date": DUE_DATE}
        ).status_code
        == 404
    )
    assert client.patch("/api/courses/9999/tasks/1", json={"active": False}).status_code == 404


def test_list_tasks_empty(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    _login(client, TEACHER)

    response = client.get(f"/api/courses/{course_id}/tasks")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_tasks_includes_active_and_inactive(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    active_id = _seed_task(app, course_id, title="Activa", active=True)
    inactive_id = _seed_task(app, course_id, title="Inactiva", active=False)
    _login(client, TEACHER)

    response = client.get(f"/api/courses/{course_id}/tasks")
    assert response.status_code == 200
    body = response.get_json()
    assert [task["id"] for task in body] == [active_id, inactive_id]
    assert [task["active"] for task in body] == [True, False]
    assert set(body[0]) == TASK_FIELDS


def test_get_task_success(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, title="Parcial 1", description="Unidad 1")
    _login(client, TEACHER)

    response = client.get(f"/api/courses/{course_id}/tasks/{task_id}")
    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == TASK_FIELDS
    assert body["id"] == task_id
    assert body["course_id"] == course_id
    assert body["title"] == "Parcial 1"
    assert body["description"] == "Unidad 1"
    assert body["active"] is True


def test_get_task_not_found(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]
    assert client.get(f"/api/courses/{course_id}/tasks/9999").status_code == 404


def test_get_task_from_other_course(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, code="PROG1")
    other_id = _seed_course(app, code="PROG2")
    _assign_teacher(app, course_id, teacher_id)
    _assign_teacher(app, other_id, teacher_id)
    task_id = _seed_task(app, other_id, title="De otro curso")
    _login(client, TEACHER)

    assert client.get(f"/api/courses/{course_id}/tasks/{task_id}").status_code == 404


def test_create_task_success(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    _login(client, TEACHER)

    response = client.post(
        f"/api/courses/{course_id}/tasks",
        json={"title": "Trabajo Práctico", "description": "Entrega grupal", "due_date": DUE_DATE},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert set(body) == TASK_FIELDS
    assert body["course_id"] == course_id
    assert body["title"] == "Trabajo Práctico"
    assert body["description"] == "Entrega grupal"
    assert body["active"] is True
    assert body["due_date"].startswith("2026-12-01T10:00:00")


def test_create_task_without_description(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(
        f"/api/courses/{course_id}/tasks", json={"title": "Sin descripción", "due_date": DUE_DATE}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["description"] == ""
    assert body["active"] is True


def test_create_task_accepts_iso_z_suffix(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(
        f"/api/courses/{course_id}/tasks", json={"title": "UTC", "due_date": DUE_DATE_Z}
    )
    assert response.status_code == 201
    assert response.get_json()["due_date"].startswith("2026-12-01T13:00:00")


def test_create_task_missing_title(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(f"/api/courses/{course_id}/tasks", json={"due_date": DUE_DATE})
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert _count_tasks(app, course_id) == 0


def test_create_task_empty_title(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(
        f"/api/courses/{course_id}/tasks", json={"title": "   ", "due_date": DUE_DATE}
    )
    assert response.status_code == 400
    assert _count_tasks(app, course_id) == 0


def test_create_task_missing_due_date(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(f"/api/courses/{course_id}/tasks", json={"title": "Sin fecha"})
    assert response.status_code == 400
    assert _count_tasks(app, course_id) == 0


def test_create_task_invalid_due_date(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(
        f"/api/courses/{course_id}/tasks", json={"title": "Fecha mala", "due_date": "not-a-date"}
    )
    assert response.status_code == 400
    assert _count_tasks(app, course_id) == 0


def test_create_task_in_inactive_course(client, app):
    _teacher_with_course(client, app, course_active=False)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.post(
        f"/api/courses/{course_id}/tasks", json={"title": "No permitida", "due_date": DUE_DATE}
    )
    assert response.status_code == 409
    assert _count_tasks(app, course_id) == 0


def test_update_task_title_and_description(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, title="Viejo", description="Vieja")
    _login(client, TEACHER)

    response = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}",
        json={"title": "Nuevo", "description": "Nueva", "due_date": DUE_DATE},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["title"] == "Nuevo"
    assert body["description"] == "Nueva"
    assert body["due_date"].startswith("2026-12-01T10:00:00")


def test_update_task_due_date(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id)
    _login(client, TEACHER)

    response = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}",
        json={"title": "Tarea", "due_date": NEW_DUE_DATE},
    )
    assert response.status_code == 200
    assert response.get_json()["due_date"].startswith("2027-01-15T08:30:00")


def test_update_task_invalid_data(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, title="Original", description="Original")
    _login(client, TEACHER)

    empty_title = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}",
        json={"title": "", "due_date": DUE_DATE},
    )
    assert empty_title.status_code == 400

    bad_date = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}",
        json={"title": "X", "due_date": "no-date"},
    )
    assert bad_date.status_code == 400

    missing_date = client.put(f"/api/courses/{course_id}/tasks/{task_id}", json={"title": "X"})
    assert missing_date.status_code == 400

    unchanged = client.get(f"/api/courses/{course_id}/tasks/{task_id}").get_json()
    assert unchanged["title"] == "Original"
    assert unchanged["description"] == "Original"


def test_update_task_in_inactive_course(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, active=False)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, title="Original")
    _login(client, TEACHER)

    response = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}",
        json={"title": "Cambio", "due_date": DUE_DATE},
    )
    assert response.status_code == 409
    unchanged = client.get(f"/api/courses/{course_id}/tasks/{task_id}").get_json()
    assert unchanged["title"] == "Original"


def test_update_task_not_found(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.put(
        f"/api/courses/{course_id}/tasks/9999",
        json={"title": "X", "due_date": DUE_DATE},
    )
    assert response.status_code == 404


def test_update_task_from_other_course(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, code="PROG1")
    other_id = _seed_course(app, code="PROG2")
    _assign_teacher(app, course_id, teacher_id)
    _assign_teacher(app, other_id, teacher_id)
    task_id = _seed_task(app, other_id, title="De otro curso")
    _login(client, TEACHER)

    response = client.put(
        f"/api/courses/{course_id}/tasks/{task_id}",
        json={"title": "Hack", "due_date": DUE_DATE},
    )
    assert response.status_code == 404


def test_patch_deactivate_and_reactivate(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, active=True)
    _login(client, TEACHER)

    deactivate = client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={"active": False})
    assert deactivate.status_code == 200
    assert deactivate.get_json()["active"] is False

    listed = client.get(f"/api/courses/{course_id}/tasks").get_json()
    assert listed[0]["active"] is False  # no se elimina

    reactivate = client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={"active": True})
    assert reactivate.status_code == 200
    assert reactivate.get_json()["active"] is True


def test_patch_missing_active_flag(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, active=True)
    _login(client, TEACHER)

    response = client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={})
    assert response.status_code == 400
    assert client.get(f"/api/courses/{course_id}/tasks/{task_id}").get_json()["active"] is True


def test_patch_non_boolean_active_flag(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, active=True)
    _login(client, TEACHER)

    response = client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={"active": "yes"})
    assert response.status_code == 400


def test_patch_task_not_found(client, app):
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]

    response = client.patch(f"/api/courses/{course_id}/tasks/9999", json={"active": False})
    assert response.status_code == 404


def test_patch_task_from_other_course(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, code="PROG1")
    other_id = _seed_course(app, code="PROG2")
    _assign_teacher(app, course_id, teacher_id)
    _assign_teacher(app, other_id, teacher_id)
    task_id = _seed_task(app, other_id)
    _login(client, TEACHER)

    assert (
        client.patch(
            f"/api/courses/{course_id}/tasks/{task_id}", json={"active": False}
        ).status_code
        == 404
    )


def test_patch_allowed_on_inactive_course(client, app):
    teacher_id = _create_user(app, TEACHER, UserRole.TEACHER)
    course_id = _seed_course(app, active=False)
    _assign_teacher(app, course_id, teacher_id)
    task_id = _seed_task(app, course_id, active=True)
    _login(client, TEACHER)

    response = client.patch(f"/api/courses/{course_id}/tasks/{task_id}", json={"active": False})
    assert response.status_code == 200
    assert response.get_json()["active"] is False


def test_manage_tasks_sends_no_email(client, app):
    """La gestión de tareas no debe registrar ningún subsistema de correo."""
    assert set(app.extensions) == set() or not any(
        "mail" in name.lower() for name in app.extensions
    )
    _teacher_with_course(client, app)
    course_id = client.get("/api/courses/mine").get_json()[0]["id"]
    created = client.post(
        f"/api/courses/{course_id}/tasks", json={"title": "T", "due_date": DUE_DATE}
    )
    assert created.status_code == 201
    # No hay mailer configurado: la operación sólo persiste y devuelve la tarea.
    assert "mail" not in created.get_json()
