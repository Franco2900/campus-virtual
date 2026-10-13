"""Portable end-to-end smoke test for the CU-06 (task management) flow.

Requires the backend (and the Vite proxy) to be running with the admin already
seeded; `scripts/verify.py --cu cu06` handles that with an isolated database.
Reads the admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD,
falling back to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu06.py [--base http://127.0.0.1:5000]

Exit code is 0 when every step PASSes, 1 otherwise.
"""

import argparse
import http.cookiejar
import json
import os
import sys
import uuid
import urllib.error
import urllib.request

DEFAULT_ADMIN_EMAIL = "admin@smoke.test"
DEFAULT_ADMIN_PASSWORD = "smoke-admin-123"
VALID_DUE_DATE = "2030-01-01T12:00:00Z"


def new_opener():
    cookies = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))


def request(base, method, path, body=None, opener=None):
    if opener is None:
        opener = urllib.request.build_opener()
    url = base + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        response = opener.open(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    raw = response.read().decode("utf-8")
    try:
        payload = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        payload = raw
    return response.status, payload


def register_user(base, opener, label):
    email = f"smoke-{label}-{uuid.uuid4()}@example.com"
    status, user = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "Smoke",
            "last_name": label.title(),
            "email": email,
            "password": "smoke12345",
        },
        opener,
    )
    user_id = user.get("id") if isinstance(user, dict) else None
    return email, user_id, status


def login(base, opener, email, password="smoke12345"):
    return request(base, "POST", "/api/auth/login", {"email": email, "password": password}, opener)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_email = os.environ.get("CAMPUS_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    admin_password = os.environ.get("CAMPUS_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    anonymous = new_opener()
    student = new_opener()
    admin = new_opener()
    teacher = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # Anonymous access is rejected.
    status, _ = request(base, "GET", "/api/courses/1/tasks", opener=anonymous)
    check("listar tareas sin sesión (401)", status == 401, f"status={status}")

    # A student is authenticated but not authorized (CU-06 actor is teacher only).
    student_email, student_id, _ = register_user(base, student, "est")
    login(base, student, student_email)
    status, _ = request(base, "GET", "/api/courses/1/tasks", opener=student)
    check("estudiante no autorizado en tareas (403)", status == 403, f"status={status}")

    # Admin login.
    status, login_data = request(
        base, "POST", "/api/auth/login", {"email": admin_email, "password": admin_password}, admin
    )
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login_data, dict) and login_data.get("role") == "admin",
        f"status={status}",
    )

    # Admin is not an allowed actor for task management (only the teacher is).
    status, _ = request(base, "GET", "/api/courses/1/tasks", opener=admin)
    check("admin no autorizado en tareas (403)", status == 403, f"status={status}")

    # Pick demo courses: two active and one inactive.
    status, courses = request(base, "GET", "/api/courses", opener=admin)
    courses = courses if isinstance(courses, list) else []
    active_courses = [course for course in courses if course.get("active")]
    inactive_courses = [course for course in courses if not course.get("active")]
    check(
        "hay cursos activos e inactivos para el smoke",
        len(active_courses) >= 2 and len(inactive_courses) >= 1,
        f"activos={len(active_courses)} inactivos={len(inactive_courses)}",
    )
    if len(active_courses) < 2 or not inactive_courses:
        print("\nSmoke CU-06: abortado — datos de demo insuficientes.")
        sys.exit(1)
    primary = active_courses[0]["id"]
    secondary = active_courses[1]["id"]
    inactive = inactive_courses[0]["id"]

    # Provision a teacher assigned only to the primary course.
    teacher_email, teacher_id, _ = register_user(base, new_opener(), "prof")
    status, _ = request(
        base,
        "PUT",
        f"/api/users/{teacher_id}",
        {"first_name": "Smoke", "last_name": "Prof", "email": teacher_email, "role": "teacher"},
        admin,
    )
    check("promover a Profesor (200)", status == 200, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/teachers", {"teacher_id": teacher_id}, admin
    )
    check("asignar profesor al curso primario (201)", status == 201, f"status={status}")

    status, _ = login(base, teacher, teacher_email)
    check("login profesor (200)", status == 200, f"status={status}")

    status, mine = request(base, "GET", "/api/courses/mine", opener=teacher)
    mine_ids = [course.get("id") for course in mine] if isinstance(mine, list) else []
    check(
        "profesor ve sólo su curso en /mine (200)",
        status == 200 and mine_ids == [primary],
        f"status={status} ids={mine_ids}",
    )

    # Empty listing.
    status, listed = request(base, "GET", f"/api/courses/{primary}/tasks", opener=teacher)
    check("listar tareas del curso vacío (200 [])", status == 200 and listed == [], f"status={status}")

    # Create a task with all fields.
    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo práctico 1", "description": "Resolver la guía", "due_date": VALID_DUE_DATE},
        teacher,
    )
    task_id = created.get("id") if isinstance(created, dict) else None
    check(
        "crear tarea (201, activa, del curso)",
        status == 201
        and isinstance(created, dict)
        and created.get("active") is True
        and created.get("course_id") == primary
        and created.get("title") == "Trabajo práctico 1",
        f"status={status}",
    )

    # Create a task without description.
    status, minimal = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Consigna sin descripción", "due_date": VALID_DUE_DATE},
        teacher,
    )
    check(
        "crear tarea sin description (201, queda vacía)",
        status == 201 and isinstance(minimal, dict) and minimal.get("description") == "",
        f"status={status}",
    )

    # Invalid payloads.
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/tasks", {"due_date": VALID_DUE_DATE}, teacher
    )
    check("crear tarea sin título (400)", status == 400, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/tasks", {"title": "   ", "due_date": VALID_DUE_DATE}, teacher
    )
    check("crear tarea con título vacío (400)", status == 400, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/tasks", {"title": "Sin fecha"}, teacher
    )
    check("crear tarea sin fecha límite (400)", status == 400, f"status={status}")
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Fecha rota", "due_date": "no-es-fecha"},
        teacher,
    )
    check("crear tarea con fecha inválida (400)", status == 400, f"status={status}")

    # The listing now includes both tasks.
    status, listed = request(base, "GET", f"/api/courses/{primary}/tasks", opener=teacher)
    check(
        "listar tareas del curso (200, incluye las creadas)",
        status == 200 and isinstance(listed, list) and len(listed) == 2,
        f"status={status} count={len(listed) if isinstance(listed, list) else 'n/a'}",
    )

    # Get a single task and a missing one.
    status, fetched = request(base, "GET", f"/api/courses/{primary}/tasks/{task_id}", opener=teacher)
    check(
        "consultar una tarea (200)",
        status == 200 and isinstance(fetched, dict) and fetched.get("id") == task_id,
        f"status={status}",
    )
    status, _ = request(base, "GET", f"/api/courses/{primary}/tasks/999999", opener=teacher)
    check("consultar tarea inexistente (404)", status == 404, f"status={status}")

    # Update the due date (alternative flow A1).
    new_due_date = "2031-06-30T09:00:00Z"
    status, updated = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}",
        {"title": "Trabajo práctico 1 (revisado)", "due_date": new_due_date},
        teacher,
    )
    check(
        "modificar fecha límite y título (200)",
        status == 200
        and isinstance(updated, dict)
        and updated.get("title") == "Trabajo práctico 1 (revisado)"
        and updated.get("description") == "",
        f"status={status}",
    )
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}",
        {"title": "", "due_date": new_due_date},
        teacher,
    )
    check("modificar con título inválido (400)", status == 400, f"status={status}")

    # Toggle active state.
    status, patched = request(
        base, "PATCH", f"/api/courses/{primary}/tasks/{task_id}", {"active": False}, teacher
    )
    check(
        "desactivar tarea (200, active=false)",
        status == 200 and isinstance(patched, dict) and patched.get("active") is False,
        f"status={status}",
    )
    status, patched = request(
        base, "PATCH", f"/api/courses/{primary}/tasks/{task_id}", {"active": True}, teacher
    )
    check(
        "reactivar tarea (200, active=true)",
        status == 200 and isinstance(patched, dict) and patched.get("active") is True,
        f"status={status}",
    )
    status, _ = request(
        base, "PATCH", f"/api/courses/{primary}/tasks/{task_id}", {"active": "yes"}, teacher
    )
    check("active inválido (400)", status == 400, f"status={status}")

    # Teacher cannot touch foreign or missing courses.
    status, _ = request(base, "GET", f"/api/courses/{secondary}/tasks", opener=teacher)
    check("profesor no ve tareas de curso ajeno (403)", status == 403, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{secondary}/tasks", {"title": "X", "due_date": VALID_DUE_DATE}, teacher
    )
    check("profesor no crea tareas en curso ajeno (403)", status == 403, f"status={status}")
    status, _ = request(base, "GET", "/api/courses/999999/tasks", opener=teacher)
    check("listar tareas de curso inexistente (404)", status == 404, f"status={status}")

    # Inactive course: task creation is blocked, but the existing task can be toggled.
    status, _ = request(
        base, "POST", f"/api/courses/{inactive}/teachers", {"teacher_id": teacher_id}, admin
    )
    check("asignar profesor al curso inactivo (201)", status == 201, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{inactive}/tasks", {"title": "Y", "due_date": VALID_DUE_DATE}, teacher
    )
    check("crear tarea en curso inactivo (409)", status == 409, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-06: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
