"""Portable end-to-end smoke test for the CU-07 (submit task) flow.

Requires the backend (and the Vite proxy) to be running with the admin already
seeded; `scripts/verify.py --cu cu07` handles that with an isolated database.
Reads the admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD,
falling back to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu07.py [--base http://127.0.0.1:5000]

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
AVAILABLE_DUE = "2030-01-01T12:00:00Z"
PAST_DUE = "2020-01-01T12:00:00Z"


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
    status, _ = request(
        base, "POST", "/api/courses/1/tasks/1/submission", {"content": "x"}, anonymous
    )
    check("entregar sin sesión (401)", status == 401, f"status={status}")

    # Register and authenticate a student.
    student_email, student_id, _ = register_user(base, student, "est")
    status, _ = login(base, student, student_email)
    check("login estudiante (200)", status == 200, f"status={status}")

    # Admin login.
    status, login_data = request(
        base, "POST", "/api/auth/login", {"email": admin_email, "password": admin_password}, admin
    )
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login_data, dict) and login_data.get("role") == "admin",
        f"status={status}",
    )

    # Pick demo courses: at least two active and one inactive.
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
        print("\nSmoke CU-07: abortado — datos de demo insuficientes.")
        sys.exit(1)
    primary = active_courses[0]["id"]
    secondary = active_courses[1]["id"]

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

    # Teacher creates three tasks: available, past-due and one that is deactivated.
    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo disponible", "due_date": AVAILABLE_DUE},
        teacher,
    )
    available_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea disponible (201)", status == 201, f"status={status}")

    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo vencido", "due_date": PAST_DUE},
        teacher,
    )
    past_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea vencida (201)", status == 201, f"status={status}")

    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo inactivo", "due_date": AVAILABLE_DUE},
        teacher,
    )
    inactive_task = created.get("id") if isinstance(created, dict) else None
    status, _ = request(
        base, "PATCH", f"/api/courses/{primary}/tasks/{inactive_task}", {"active": False}, teacher
    )
    check("desactivar la tercera tarea (200)", status == 200, f"status={status}")

    # A free available task used to exercise "submission not found".
    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo sin entregar", "due_date": AVAILABLE_DUE},
        teacher,
    )
    free_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea sin entregar (201)", status == 201, f"status={status}")

    # Student is not enrolled yet: /mine hides the course and the API forbids it.
    status, mine = request(base, "GET", "/api/courses/mine", opener=student)
    mine_ids = [course.get("id") for course in mine] if isinstance(mine, list) else []
    check(
        "estudiante sin inscripción: /mine no incluye el curso (200)",
        status == 200 and primary not in mine_ids,
        f"status={status} ids={mine_ids}",
    )
    status, _ = request(base, "GET", f"/api/courses/{primary}/tasks", opener=student)
    check("estudiante sin inscripción no lista tareas (403)", status == 403, f"status={status}")
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "Antes de inscribirme"},
        student,
    )
    check("estudiante sin inscripción no entrega (403)", status == 403, f"status={status}")

    # Admin enrolls the student in the primary course.
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": student_id}, admin
    )
    check("inscribir estudiante (201)", status == 201, f"status={status}")

    status, mine = request(base, "GET", "/api/courses/mine", opener=student)
    mine_ids = [course.get("id") for course in mine] if isinstance(mine, list) else []
    check(
        "estudiante ve su curso inscripto en /mine (200)",
        status == 200 and primary in mine_ids,
        f"status={status} ids={mine_ids}",
    )

    # Student listing: only the available tasks, with a null submission.
    status, listed = request(base, "GET", f"/api/courses/{primary}/tasks", opener=student)
    listed_ids = [task.get("id") for task in listed] if isinstance(listed, list) else []
    check(
        "estudiante sólo ve tareas disponibles (200: disponible y sin entregar)",
        status == 200 and set(listed_ids) == {available_task, free_task},
        f"status={status} ids={listed_ids}",
    )
    check(
        "cada tarea del estudiante incluye submission=null",
        isinstance(listed, list)
        and all(task.get("submission") is None for task in listed),
    )

    # Teacher listing keeps the original shape: no "submission" key.
    status, teacher_listed = request(base, "GET", f"/api/courses/{primary}/tasks", opener=teacher)
    check(
        "profesor ve todas las tareas sin clave submission",
        status == 200
        and isinstance(teacher_listed, list)
        and len(teacher_listed) == 4
        and all("submission" not in task for task in teacher_listed),
        f"status={status} count={len(teacher_listed) if isinstance(teacher_listed, list) else 'n/a'}",
    )

    # Create the submission with text and links.
    status, submission = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "Mi primera entrega", "links": ["https://example.com/entrega"]},
        student,
    )
    check(
        "entregar tarea (201, contenido y enlaces)",
        status == 201
        and isinstance(submission, dict)
        and submission.get("content") == "Mi primera entrega"
        and submission.get("links") == ["https://example.com/entrega"]
        and submission.get("task_id") == available_task,
        f"status={status}",
    )

    # The listing now reports the submission.
    status, listed = request(base, "GET", f"/api/courses/{primary}/tasks", opener=student)
    row = next(
        (task for task in listed if task.get("id") == available_task), None
    ) if isinstance(listed, list) else None
    check(
        "la lista del estudiante muestra su entrega",
        isinstance(row, dict)
        and isinstance(row.get("submission"), dict)
        and row["submission"].get("content") == "Mi primera entrega",
    )

    # Duplicate submission is a conflict.
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "Otra entrega"},
        student,
    )
    check("entregar dos veces (409)", status == 409, f"status={status}")

    # Update the submission (alternative flow A1).
    status, updated = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "Entrega corregida", "links": ["https://example.com/v2", "https://example.com/v3"]},
        student,
    )
    check(
        "editar entrega (200, contenido y enlaces actualizados)",
        status == 200
        and isinstance(updated, dict)
        and updated.get("content") == "Entrega corregida"
        and updated.get("links") == ["https://example.com/v2", "https://example.com/v3"],
        f"status={status}",
    )

    # Invalid payload: empty content and no links.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "   ", "links": []},
        student,
    )
    check("editar sin texto ni enlaces (400)", status == 400, f"status={status}")

    # Invalid payload: content too long.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "x" * 5001},
        student,
    )
    check("editar con contenido demasiado largo (400)", status == 400, f"status={status}")

    # Past-due and inactive tasks cannot receive submissions.
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{past_task}/submission",
        {"content": "Fuera de plazo"},
        student,
    )
    check("entregar tarea vencida (409)", status == 409, f"status={status}")
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{inactive_task}/submission",
        {"content": "Tarea inactiva"},
        student,
    )
    check("entregar tarea inactiva (409)", status == 409, f"status={status}")

    # Unknown task and unknown course.
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/999999/submission",
        {"content": "Tarea inexistente"},
        student,
    )
    check("entregar tarea inexistente (404)", status == 404, f"status={status}")
    status, _ = request(base, "GET", "/api/courses/999999/tasks", opener=student)
    check("listar tareas de curso inexistente (404)", status == 404, f"status={status}")

    # A different active course where the student is not enrolled.
    status, _ = request(base, "GET", f"/api/courses/{secondary}/tasks", opener=student)
    check("estudiante no ve tareas de curso ajeno (403)", status == 403, f"status={status}")
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{secondary}/tasks/{available_task}/submission",
        {"content": "Curso ajeno"},
        student,
    )
    check("estudiante no entrega en curso ajeno (403)", status == 403, f"status={status}")

    # Updating a submission that does not exist.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{free_task}/submission",
        {"content": "Sin entrega previa"},
        student,
    )
    check("editar entrega inexistente (404)", status == 404, f"status={status}")

    # Only students may use the submission endpoint.
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "Profesor entrega"},
        teacher,
    )
    check("profesor no puede entregar (403)", status == 403, f"status={status}")
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"content": "Admin entrega"},
        admin,
    )
    check("admin no puede entregar (403)", status == 403, f"status={status}")

    # Delete the submission (alternative flow A2).
    status, _ = request(
        base,
        "DELETE",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        None,
        student,
    )
    check("eliminar entrega (200)", status == 200, f"status={status}")
    status, _ = request(
        base,
        "DELETE",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        None,
        student,
    )
    check("eliminar entrega inexistente (404)", status == 404, f"status={status}")

    # After deleting, the listing reports no submission again.
    status, listed = request(base, "GET", f"/api/courses/{primary}/tasks", opener=student)
    row = next(
        (task for task in listed if task.get("id") == available_task), None
    ) if isinstance(listed, list) else None
    check(
        "tras eliminar, la tarea vuelve a submission=null",
        isinstance(row, dict) and row.get("submission") is None,
    )

    # Links-only submission is valid.
    status, submission = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{available_task}/submission",
        {"links": ["https://example.com/solo-enlace"]},
        student,
    )
    check(
        "entregar sólo con enlaces (201, contenido vacío)",
        status == 201
        and isinstance(submission, dict)
        and submission.get("content") == ""
        and submission.get("links") == ["https://example.com/solo-enlace"],
        f"status={status}",
    )

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-07: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
