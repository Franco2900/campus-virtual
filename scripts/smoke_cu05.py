"""Portable end-to-end smoke test for the CU-05 (enrollment management) flow.

Requires the backend (and the Vite proxy) to be running with the admin already
seeded; `scripts/verify.py --cu cu05` handles that with an isolated database.
Reads the admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD,
falling back to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu05.py [--base http://127.0.0.1:5000]

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


def register_student(base, opener, label):
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

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # Anonymous access is rejected.
    status, _ = request(base, "GET", "/api/courses/1/students", opener=anonymous)
    check("listar estudiantes sin sesión (401)", status == 401, f"status={status}")

    # A student is authenticated but not authorized.
    student_email, student_id, _ = register_student(base, student, "est")
    login(base, student, student_email)
    status, _ = request(base, "GET", "/api/courses/1/students", opener=student)
    check("estudiante no autorizado en inscripciones (403)", status == 403, f"status={status}")
    status, _ = request(base, "GET", "/api/courses/mine", opener=student)
    check("estudiante no autorizado en /mine (403)", status == 403, f"status={status}")

    # Admin login.
    status, login_data = request(
        base, "POST", "/api/auth/login", {"email": admin_email, "password": admin_password}, admin
    )
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login_data, dict) and login_data.get("role") == "admin",
        f"status={status}",
    )

    # Pick demo courses: two active (primary/secondary) and one inactive.
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
        print("\nSmoke CU-05: abortado — datos de demo insuficientes.")
        sys.exit(1)
    primary = active_courses[0]["id"]
    secondary = active_courses[1]["id"]
    inactive = inactive_courses[0]["id"]

    # Admin manages enrollments with full scope.
    status, mine = request(base, "GET", "/api/courses/mine", opener=admin)
    check(
        "admin ve todos los cursos en /mine (200)",
        status == 200 and isinstance(mine, list) and len(mine) == len(courses),
        f"status={status} count={len(mine) if isinstance(mine, list) else 'n/a'}",
    )

    status, enrolled = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": student_id}, admin
    )
    check(
        "inscribir estudiante (201, enrollment activo)",
        status == 201
        and isinstance(enrolled, dict)
        and enrolled.get("role") == "student"
        and isinstance(enrolled.get("enrollment"), dict)
        and enrolled["enrollment"].get("active") is True,
        f"status={status}",
    )

    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": student_id}, admin
    )
    check("inscripción duplicada (409)", status == 409, f"status={status}")

    status, listed = request(base, "GET", f"/api/courses/{primary}/students", opener=admin)
    row = next((item for item in listed if item.get("id") == student_id), None) if listed else None
    check(
        "listar estudiantes del curso (200, con inscripción nidada)",
        status == 200
        and row is not None
        and isinstance(row.get("enrollment"), dict)
        and row["enrollment"].get("active") is True,
        f"status={status}",
    )

    status, patched = request(
        base, "PATCH", f"/api/courses/{primary}/students/{student_id}", {"active": False}, admin
    )
    check(
        "desactivar inscripción (200, active=false)",
        status == 200
        and isinstance(patched, dict)
        and patched.get("enrollment", {}).get("active") is False,
        f"status={status}",
    )

    status, patched = request(
        base, "PATCH", f"/api/courses/{primary}/students/{student_id}", {"active": True}, admin
    )
    check(
        "reactivar inscripción (200, active=true)",
        status == 200
        and isinstance(patched, dict)
        and patched.get("enrollment", {}).get("active") is True,
        f"status={status}",
    )

    status, _ = request(
        base, "PATCH", f"/api/courses/{primary}/students/{student_id}", {"active": "yes"}, admin
    )
    check("active inválido (400)", status == 400, f"status={status}")

    # Course must be active to enroll.
    status, _ = request(
        base, "POST", f"/api/courses/{inactive}/students", {"student_id": student_id}, admin
    )
    check("inscribir en curso inactivo (409)", status == 409, f"status={status}")

    # Student must exist and be an active student account.
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": 999999}, admin
    )
    check("inscribir estudiante inexistente (404)", status == 404, f"status={status}")

    status, _ = request(base, "POST", "/api/courses/999999/students", {"student_id": student_id}, admin)
    check("inscribir en curso inexistente (404)", status == 404, f"status={status}")

    # Non-student accounts are rejected.
    teacher_email, teacher_id, _ = register_student(base, new_opener(), "prof")
    status, _ = request(
        base,
        "PUT",
        f"/api/users/{teacher_id}",
        {"first_name": "Smoke", "last_name": "Prof", "email": teacher_email, "role": "teacher"},
        admin,
    )
    check("promover a Profesor (200)", status == 200, f"status={status}")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": teacher_id}, admin
    )
    check("inscribir una cuenta no-estudiante (400)", status == 400, f"status={status}")

    # Inactive accounts are rejected.
    inactive_email, inactive_id, _ = register_student(base, new_opener(), "inactivo")
    request(base, "PATCH", f"/api/users/{inactive_id}", {"active": False}, admin)
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": inactive_id}, admin
    )
    check("inscribir una cuenta inactiva (400)", status == 400, f"status={status}")

    # Remove the enrollment (physical delete) and confirm it is gone.
    status, _ = request(
        base, "DELETE", f"/api/courses/{primary}/students/{student_id}", opener=admin
    )
    check("eliminar inscripción (200)", status == 200, f"status={status}")

    status, listed = request(base, "GET", f"/api/courses/{primary}/students", opener=admin)
    row = next((item for item in listed if item.get("id") == student_id), None) if listed else None
    check(
        "tras eliminar, la inscripción queda ausente (enrollment null)",
        status == 200 and row is not None and row.get("enrollment") is None,
        f"status={status}",
    )

    status, _ = request(
        base, "DELETE", f"/api/courses/{primary}/students/{student_id}", opener=admin
    )
    check("eliminar inscripción inexistente (404)", status == 404, f"status={status}")

    status, _ = request(base, "GET", "/api/courses/999999/students", opener=admin)
    check("listar estudiantes de curso inexistente (404)", status == 404, f"status={status}")

    # Teacher scope: only assigned courses, and cannot touch foreign courses.
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/teachers", {"teacher_id": teacher_id}, admin
    )
    check("asignar profesor al curso primario (201)", status == 201, f"status={status}")

    teacher = new_opener()
    status, _ = login(base, teacher, teacher_email)
    check("login profesor (200)", status == 200, f"status={status}")

    status, mine = request(base, "GET", "/api/courses/mine", opener=teacher)
    mine_ids = [course.get("id") for course in mine] if isinstance(mine, list) else []
    check(
        "profesor ve sólo su curso en /mine (200)",
        status == 200 and mine_ids == [primary],
        f"status={status} ids={mine_ids}",
    )

    st2_email, st2_id, _ = register_student(base, new_opener(), "est2")
    status, _ = request(
        base, "POST", f"/api/courses/{primary}/students", {"student_id": st2_id}, teacher
    )
    check("profesor inscribe en su curso (201)", status == 201, f"status={status}")

    status, _ = request(base, "GET", f"/api/courses/{secondary}/students", opener=teacher)
    check("profesor no ve curso ajeno (403)", status == 403, f"status={status}")

    status, _ = request(
        base, "POST", f"/api/courses/{secondary}/students", {"student_id": st2_id}, teacher
    )
    check("profesor no inscribe en curso ajeno (403)", status == 403, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-05: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
