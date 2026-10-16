"""Portable end-to-end smoke test for the CU-09 (consult grades) flow.

Exercises GET /api/courses/<id>/grades against the role-aware view: a Student
sees their own detail plus the course average, a Teacher sees the student x task
matrix plus the course average, and 401/403/404 are enforced. Requires the
backend (and the Vite proxy) to be running with the admin already seeded;
`scripts/verify.py --cu cu09` handles that with an isolated database. Reads the
admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD, falling back
to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu09.py [--base http://127.0.0.1:5000]

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
PAST_DUE = "2000-01-01T00:00:00Z"
STUDENT_TASK_FIELDS = {
    "task_id",
    "title",
    "due_date",
    "active",
    "submitted",
    "grade",
    "feedback",
    "graded_at",
    "approved",
    "counted",
    "effective_value",
}
STUDENT_VIEW_FIELDS = {"course", "average", "tasks"}
TEACHER_VIEW_FIELDS = {"course", "tasks", "students", "course_average"}
TEACHER_TASK_FIELDS = {"task_id", "title", "due_date", "active"}


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


def promote_to_teacher(base, admin, user_id, email):
    status, _ = request(
        base,
        "PUT",
        f"/api/users/{user_id}",
        {"first_name": "Smoke", "last_name": "Prof", "email": email, "role": "teacher"},
        admin,
    )
    return status


def grades_url(course_id):
    return f"/api/courses/{course_id}/grades"


def find_task(tasks, task_id):
    if not isinstance(tasks, list):
        return None
    return next((task for task in tasks if task.get("task_id") == task_id), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_email = os.environ.get("CAMPUS_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    admin_password = os.environ.get("CAMPUS_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    anonymous = new_opener()
    student = new_opener()
    other_student = new_opener()
    unenrolled = new_opener()
    admin = new_opener()
    teacher = new_opener()
    other_teacher = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # Anonymous access is rejected (401) before any role/course check.
    status, _ = request(base, "GET", grades_url(1), opener=anonymous)
    check("consultar calificaciones sin sesión (401)", status == 401, f"status={status}")

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
        print("\nSmoke CU-09: abortado — datos de demo insuficientes.")
        sys.exit(1)
    primary = active_courses[0]["id"]
    secondary = active_courses[1]["id"]

    # Provision the primary teacher (assigned only to the primary course).
    teacher_email, teacher_id, _ = register_user(base, new_opener(), "prof")
    status = promote_to_teacher(base, admin, teacher_id, teacher_email)
    check("promover a Profesor (200)", status == 200, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/teachers", {"teacher_id": teacher_id}, admin
    )
    check("asignar profesor al curso primario (201)", status == 201, f"status={status}")
    status, _ = login(base, teacher, teacher_email)
    check("login profesor asignado (200)", status == 200, f"status={status}")

    # Provision a second teacher assigned only to the secondary course.
    other_email, other_id, _ = register_user(base, new_opener(), "prof2")
    status = promote_to_teacher(base, admin, other_id, other_email)
    check("promover al segundo Profesor (200)", status == 200, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{secondary}/teachers", {"teacher_id": other_id}, admin
    )
    check("asignar segundo profesor al curso secundario (201)", status == 201, f"status={status}")
    status, _ = login(base, other_teacher, other_email)
    check("login profesor no asignado al curso primario (200)", status == 200, f"status={status}")

    # Admin enrolls the student in the primary course.
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": student_id}, admin
    )
    check("inscribir estudiante en el curso primario (201)", status == 201, f"status={status}")

    # Primary teacher creates one graded task (future due) and one expired task
    # with no submission (contributes 1 to the average).
    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo a corregir", "due_date": AVAILABLE_DUE},
        teacher,
    )
    graded_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea a corregir (201)", status == 201, f"status={status}")

    status, created = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks",
        {"title": "Trabajo vencido sin entrega", "due_date": PAST_DUE},
        teacher,
    )
    expired_task = created.get("id") if isinstance(created, dict) else None
    check("crear tarea vencida sin entrega (201)", status == 201, f"status={status}")

    # Student submits the graded task; the teacher grades it.
    status, _ = request(
        base,
        "POST",
        f"/api/courses/{primary}/tasks/{graded_task}/submission",
        {"content": "Mi entrega", "links": ["https://example.com/entrega"]},
        student,
    )
    check("estudiante entrega la tarea (201)", status == 201, f"status={status}")
    status, _ = request(
        base,
        "PUT",
        f"/api/courses/{primary}/tasks/{graded_task}/submissions/{student_id}/grade",
        {"grade": 8, "feedback": "Muy bien"},
        teacher,
    )
    check("profesor corrige la entrega (200, grade=8)", status == 200, f"status={status}")

    # Student view: own detail plus average (8 for the graded task, 1 for the
    # expired task without submission -> 4.5).
    status, student_body = request(base, "GET", grades_url(primary), opener=student)
    check(
        "estudiante consulta sus calificaciones (200)",
        status == 200 and isinstance(student_body, dict),
        f"status={status}",
    )
    check(
        "vista del estudiante con el conjunto de campos esperado",
        isinstance(student_body, dict) and set(student_body) == STUDENT_VIEW_FIELDS,
        f"claves={sorted(student_body) if isinstance(student_body, dict) else 'n/a'}",
    )
    check(
        "el estudiante ve su promedio (8 y 1 -> 4.5)",
        isinstance(student_body, dict) and student_body.get("average") == 4.5,
        f"average={student_body.get('average') if isinstance(student_body, dict) else 'n/a'}",
    )
    detail = find_task(student_body.get("tasks"), graded_task) if isinstance(student_body, dict) else None
    check(
        "la tarea corregida expone nota, retroalimentación y aprobación",
        isinstance(detail, dict)
        and set(detail) == STUDENT_TASK_FIELDS
        and detail.get("submitted") is True
        and detail.get("grade") == 8
        and detail.get("feedback") == "Muy bien"
        and detail.get("approved") is True
        and detail.get("counted") is True
        and detail.get("effective_value") == 8,
        f"detalle={detail}",
    )
    expired_detail = (
        find_task(student_body.get("tasks"), expired_task) if isinstance(student_body, dict) else None
    )
    check(
        "la tarea vencida sin entrega aporta 1 y no está aprobada",
        isinstance(expired_detail, dict)
        and expired_detail.get("submitted") is False
        and expired_detail.get("grade") is None
        and expired_detail.get("approved") is False
        and expired_detail.get("counted") is True
        and expired_detail.get("effective_value") == 1,
        f"detalle={expired_detail}",
    )

    # Teacher view: students x tasks matrix plus the course average.
    status, teacher_body = request(base, "GET", grades_url(primary), opener=teacher)
    check(
        "profesor asignado consulta la matriz (200)",
        status == 200 and isinstance(teacher_body, dict),
        f"status={status}",
    )
    check(
        "vista del profesor con el conjunto de campos esperado",
        isinstance(teacher_body, dict) and set(teacher_body) == TEACHER_VIEW_FIELDS,
        f"claves={sorted(teacher_body) if isinstance(teacher_body, dict) else 'n/a'}",
    )
    matrix_task_ids = (
        [task.get("task_id") for task in teacher_body.get("tasks", [])]
        if isinstance(teacher_body, dict)
        else []
    )
    check(
        "la matriz tiene por columnas las tareas activas",
        set(matrix_task_ids) == {graded_task, expired_task}
        and all(
            set(task) == TEACHER_TASK_FIELDS for task in teacher_body.get("tasks", [])
        ),
        f"tasks={matrix_task_ids}",
    )
    rows = teacher_body.get("students", []) if isinstance(teacher_body, dict) else []
    row = next((item for item in rows if item.get("student", {}).get("id") == student_id), None)
    check(
        "la matriz tiene una fila por estudiante inscripto con su promedio",
        isinstance(row, dict)
        and row.get("grades") == {str(graded_task): 8, str(expired_task): 1}
        and row.get("average") == 4.5,
        f"fila={row}",
    )
    check(
        "la fila del estudiante expone su estado de aprobación del curso",
        isinstance(row, dict) and row.get("approved") is False,
        f"approved={row.get('approved') if isinstance(row, dict) else 'n/a'}",
    )
    check(
        "el promedio del curso es la media de los promedios por estudiante",
        isinstance(teacher_body, dict) and teacher_body.get("course_average") == 4.5,
        f"course_average={teacher_body.get('course_average') if isinstance(teacher_body, dict) else 'n/a'}",
    )

    # Isolation: a second enrolled student only sees their own grades and does
    # not change the first student's view.
    other_email2, other_student_id, _ = register_user(base, other_student, "est2")
    status, _ = login(base, other_student, other_email2)
    check("login segundo estudiante (200)", status == 200, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": other_student_id}, admin
    )
    check("inscribir segundo estudiante (201)", status == 201, f"status={status}")
    status, other_body = request(base, "GET", grades_url(primary), opener=other_student)
    check(
        "el segundo estudiante ve sólo sus calificaciones (promedio 1)",
        status == 200
        and isinstance(other_body, dict)
        and other_body.get("average") == 1
        and len(other_body.get("tasks", [])) == 2,
        f"status={status} average={other_body.get('average') if isinstance(other_body, dict) else 'n/a'}",
    )
    status, student_body_again = request(base, "GET", grades_url(primary), opener=student)
    check(
        "la vista del primer estudiante no se contamina con otro estudiante",
        status == 200
        and isinstance(student_body_again, dict)
        and student_body_again.get("average") == 4.5
        and (find_task(student_body_again.get("tasks"), graded_task) or {}).get("grade") == 8,
        f"average={student_body_again.get('average') if isinstance(student_body_again, dict) else 'n/a'}",
    )

    # Admin is not allowed to consult grades (403).
    status, _ = request(base, "GET", grades_url(primary), opener=admin)
    check("administrador no consulta calificaciones (403)", status == 403, f"status={status}")

    # Non-existent course (404) for both roles.
    status, _ = request(base, "GET", grades_url(999999), opener=student)
    check("estudiante: curso inexistente (404)", status == 404, f"status={status}")
    status, _ = request(base, "GET", grades_url(999999), opener=teacher)
    check("profesor: curso inexistente (404)", status == 404, f"status={status}")

    # Student without an active enrollment in the course (403).
    unenrolled_email, _, _ = register_user(base, unenrolled, "est3")
    status, _ = login(base, unenrolled, unenrolled_email)
    check("login estudiante sin inscripción (200)", status == 200, f"status={status}")
    status, _ = request(base, "GET", grades_url(primary), opener=unenrolled)
    check("estudiante sin inscripción activa (403)", status == 403, f"status={status}")

    # Teacher not assigned to the course (403).
    status, _ = request(base, "GET", grades_url(primary), opener=other_teacher)
    check("profesor no asignado al curso (403)", status == 403, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-09: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
