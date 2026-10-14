"""Portable end-to-end smoke test for the CU-08 (grade task) flow.

Requires the backend (and the Vite proxy) to be running with the admin already
seeded; `scripts/verify.py --cu cu08` handles that with an isolated database.
Reads the admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD,
falling back to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu08.py [--base http://127.0.0.1:5000]

Exit code is 0 when every step PASSes, 1 otherwise.
"""

import argparse
import http.cookiejar
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.request

DEFAULT_ADMIN_EMAIL = "admin@smoke.test"
DEFAULT_ADMIN_PASSWORD = "smoke-admin-123"
AVAILABLE_DUE = "2030-01-01T12:00:00Z"


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
    other_teacher = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # Anonymous access is rejected on both grading endpoints.
    status, _ = request(base, "GET", "/api/courses/1/tasks/1/submissions", opener=anonymous)
    check("listar entregas sin sesión (401)", status == 401, f"status={status}")
    status, _ = request(
        base, "PUT", "/api/courses/1/tasks/1/submissions/1/grade", {"grade": 8}, anonymous
    )
    check("corregir sin sesión (401)", status == 401, f"status={status}")

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

    # Pick demo courses: at least two active.
    status, courses = request(base, "GET", "/api/courses", opener=admin)
    courses = courses if isinstance(courses, list) else []
    active_courses = [course for course in courses if course.get("active")]
    check(
        "hay al menos dos cursos activos para el smoke",
        len(active_courses) >= 2,
        f"activos={len(active_courses)}",
    )
    if len(active_courses) < 2:
        print("\nSmoke CU-08: abortado — datos de demo insuficientes.")
        sys.exit(1)
    primary = active_courses[0]["id"]
    secondary = active_courses[1]["id"]

    # Provision the primary teacher (assigned only to the primary course).
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
    check("login profesor asignado (200)", status == 200, f"status={status}")

    # Provision a second teacher assigned only to the secondary course.
    other_email, other_id, _ = register_user(base, new_opener(), "prof2")
    status, _ = request(
        base,
        "PUT",
        f"/api/users/{other_id}",
        {"first_name": "Smoke", "last_name": "Prof2", "email": other_email, "role": "teacher"},
        admin,
    )
    check("promover al segundo Profesor (200)", status == 200, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{secondary}/teachers", {"teacher_id": other_id}, admin
    )
    check("asignar segundo profesor al curso secundario (201)", status == 201, f"status={status}")
    status, _ = login(base, other_teacher, other_email)
    check("login profesor no asignado al curso primario (200)", status == 200, f"status={status}")

    # The secondary course gets a task used to exercise "task from another course".
    status, created = request(
        base,
        "POST",
        f"/api/courses/{secondary}/tasks",
        {"title": "Tarea del curso ajeno", "due_date": AVAILABLE_DUE},
        other_teacher,
    )
    foreign_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea del curso ajeno (201)", status == 201, f"status={status}")

    # Admin enrolls the student in the primary course.
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": student_id}, admin
    )
    check("inscribir estudiante en el curso primario (201)", status == 201, f"status={status}")

    # Primary teacher creates the task to be graded plus a free task with no submission.
    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo a corregir", "due_date": AVAILABLE_DUE},
        teacher,
    )
    task_id = created.get("id") if isinstance(created, dict) else None
    check("crear tarea a corregir (201)", status == 201, f"status={status}")

    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Tarea sin entregar", "due_date": AVAILABLE_DUE},
        teacher,
    )
    free_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea sin entregar (201)", status == 201, f"status={status}")

    # Student submits the task.
    status, submission = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{task_id}/submission",
        {"content": "Mi entrega para corregir", "links": ["https://example.com/entrega"]},
        student,
    )
    check("estudiante entrega la tarea (201)", status == 201, f"status={status}")

    # 2. Assigned teacher lists the submissions: one row, student data, grade null.
    status, listed = request(
        base, "GET", f"/api/courses/{primary}/tasks/{task_id}/submissions", opener=teacher
    )
    row = listed[0] if isinstance(listed, list) and listed else None
    check(
        "profesor lista las entregas (200, incluye la entrega)",
        status == 200
        and isinstance(listed, list)
        and len(listed) == 1
        and isinstance(row, dict)
        and row.get("student_id") == student_id,
        f"status={status} count={len(listed) if isinstance(listed, list) else 'n/a'}",
    )
    check(
        "la entrega incluye los datos del estudiante",
        isinstance(row, dict)
        and isinstance(row.get("student"), dict)
        and row["student"].get("id") == student_id
        and bool(row["student"].get("email")),
    )
    check(
        "la entrega sin corregir tiene grade/feedback/graded_at nulos",
        isinstance(row, dict)
        and row.get("grade") is None
        and row.get("feedback") == ""
        and row.get("graded_at") is None
        and row.get("approved") is False,
    )

    # 3. Teacher grades the submission (approval threshold is 6).
    status, graded = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}/submissions/{student_id}/grade",
        {"grade": 8, "feedback": "Muy bien"},
        teacher,
    )
    first_graded_at = graded.get("graded_at") if isinstance(graded, dict) else None
    check(
        "corregir la entrega (200, grade=8, approved=true)",
        status == 200
        and isinstance(graded, dict)
        and graded.get("grade") == 8
        and graded.get("feedback") == "Muy bien"
        and graded.get("graded_at") is not None
        and graded.get("approved") is True,
        f"status={status}",
    )

    # 4. Teacher modifies the grade (alternative flow A1): approval flips to false.
    time.sleep(0.05)
    status, regraded = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}/submissions/{student_id}/grade",
        {"grade": 4},
        teacher,
    )
    second_graded_at = regraded.get("graded_at") if isinstance(regraded, dict) else None
    check(
        "modificar la calificación (200, grade=4, approved=false)",
        status == 200
        and isinstance(regraded, dict)
        and regraded.get("grade") == 4
        and regraded.get("approved") is False,
        f"status={status}",
    )
    check(
        "graded_at cambia tras la modificación",
        first_graded_at is not None
        and second_graded_at is not None
        and second_graded_at != first_graded_at,
        f"antes={first_graded_at} despues={second_graded_at}",
    )

    # 5. Invalid grades are rejected.
    for invalid_grade in (0, 11, "ocho"):
        status, _ = request(
            base,
            "PUT",
            f"/api/courses/{primary}/tasks/{task_id}/submissions/{student_id}/grade",
            {"grade": invalid_grade},
            teacher,
        )
        check(f"calificación inválida {invalid_grade!r} (400)", status == 400, f"status={status}")

    # 6. Feedback longer than 5000 characters is rejected.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}/submissions/{student_id}/grade",
        {"grade": 8, "feedback": "x" * 5001},
        teacher,
    )
    check("retroalimentación de 5001 caracteres (400)", status == 400, f"status={status}")

    # 7. A student cannot grade (teacher-only endpoint).
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}/submissions/{student_id}/grade",
        {"grade": 8},
        student,
    )
    check("estudiante no puede corregir (403)", status == 403, f"status={status}")

    # 8. A teacher who does not work on the course cannot grade it.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}/submissions/{student_id}/grade",
        {"grade": 8},
        other_teacher,
    )
    check("profesor no asignado no corrige (403)", status == 403, f"status={status}")

    # 9. Unknown course and task from another course are not found.
    status, _ = request(
        base, "GET", f"/api/courses/999999/tasks/{task_id}/submissions", opener=teacher
    )
    check("listar entregas de curso inexistente (404)", status == 404, f"status={status}")
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/999999/tasks/{task_id}/submissions/{student_id}/grade",
        {"grade": 8},
        teacher,
    )
    check("corregir en curso inexistente (404)", status == 404, f"status={status}")
    status, _ = request(
        base, "GET", f"/api/courses/{primary}/tasks/{foreign_task}/submissions", opener=teacher
    )
    check("listar entregas de tarea de otro curso (404)", status == 404, f"status={status}")
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{foreign_task}/submissions/{student_id}/grade",
        {"grade": 8},
        teacher,
    )
    check("corregir tarea de otro curso (404)", status == 404, f"status={status}")

    # 9b. Grading a student who never submitted is not found.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{free_task}/submissions/{student_id}/grade",
        {"grade": 8},
        teacher,
    )
    check("corregir una entrega inexistente (404)", status == 404, f"status={status}")

    # 10. CU-07 gate: a graded submission can no longer be edited or deleted.
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{task_id}/submission",
        {"content": "Intento de edición tras corrección"},
        student,
    )
    check("editar una entrega ya corregida (409)", status == 409, f"status={status}")
    status, _ = request(
        base,
        "DELETE",
        f"/api/courses/{primary}/tasks/{task_id}/submission",
        None,
        student,
    )
    check("eliminar una entrega ya corregida (409)", status == 409, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nRESULT: {total - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
