"""Portable end-to-end smoke test for the CU-04 (user management) flow.

Requires the backend (and the Vite proxy) to be running with the admin already
seeded; `scripts/verify.py --cu cu04` handles that with an isolated database.
Reads the admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD,
falling back to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu04.py [--base http://127.0.0.1:5000]

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


def register_user(base, opener, role_label):
    email = f"smoke-{role_label}-{uuid.uuid4()}@example.com"
    status, user = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "Smoke",
            "last_name": role_label.title(),
            "email": email,
            "password": "smoke12345",
        },
        opener,
    )
    user_id = user.get("id") if isinstance(user, dict) else None
    return email, user_id, status


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
    admin = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # Anonymous access is rejected.
    status, _ = request(base, "GET", "/api/users", opener=anonymous)
    check("listar usuarios sin sesión (401)", status == 401, f"status={status}")

    # A student is authenticated but not authorized.
    student_email, student_id, _ = register_user(base, student, "student")
    request(base, "POST", "/api/auth/login", {"email": student_email, "password": "smoke12345"}, student)
    status, _ = request(base, "GET", "/api/users", opener=student)
    check("estudiante no autorizado (403)", status == 403, f"status={status}")

    # Admin login.
    status, login = request(
        base, "POST", "/api/auth/login", {"email": admin_email, "password": admin_password}, admin
    )
    admin_id = login.get("id") if isinstance(login, dict) else None
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login, dict) and login.get("role") == "admin",
        f"status={status}",
    )

    # Listing includes registered users and never exposes the password.
    status, users = request(base, "GET", "/api/users", opener=admin)
    ok = status == 200 and isinstance(users, list)
    emails = {user.get("email") for user in users} if ok else set()
    leaks = any("password_hash" in user or "password" in user for user in users) if ok else True
    check(
        "listar usuarios (200, incluye registrados, sin password)",
        ok and student_email in emails and not leaks,
        f"status={status} count={len(users) if ok else 'n/a'}",
    )

    # Promote the student to Profesor.
    status, promoted = request(
        base,
        "PUT",
        f"/api/users/{student_id}",
        {
            "first_name": "Smoke",
            "last_name": "Teacher",
            "email": student_email,
            "role": "teacher",
        },
        admin,
    )
    check(
        "promover a Profesor (200, role teacher)",
        status == 200 and isinstance(promoted, dict) and promoted.get("role") == "teacher",
        f"status={status}",
    )

    # A non-teacher account cannot be assigned as a course teacher.
    other_email, other_id, _ = register_user(base, other_student, "otro")
    status, courses = request(base, "GET", "/api/courses", opener=admin)
    course_id = courses[0]["id"] if isinstance(courses, list) and courses else None
    status, _ = request(
        base, "POST", f"/api/courses/{course_id}/teachers", {"teacher_id": other_id}, admin
    )
    check("asignar no-profesor (400)", status == 400, f"status={status}")

    # Assign the professor to a course.
    status, assigned = request(
        base, "POST", f"/api/courses/{course_id}/teachers", {"teacher_id": student_id}, admin
    )
    check(
        "asignar profesor a curso (201, role teacher)",
        status == 201 and isinstance(assigned, dict) and assigned.get("role") == "teacher",
        f"status={status}",
    )

    status, _ = request(
        base, "POST", f"/api/courses/{course_id}/teachers", {"teacher_id": student_id}, admin
    )
    check("asignación duplicada (409)", status == 409, f"status={status}")

    status, teachers = request(base, "GET", f"/api/courses/{course_id}/teachers", opener=admin)
    ids = [teacher.get("id") for teacher in teachers] if isinstance(teachers, list) else []
    check(
        "listar profesores del curso (200, incluye al asignado)",
        status == 200 and student_id in ids,
        f"status={status} ids={ids}",
    )

    status, _ = request(base, "GET", "/api/courses/999999/teachers", opener=admin)
    check("curso inexistente al listar profesores (404)", status == 404, f"status={status}")

    # Reset password and verify the new password works.
    status, _ = request(
        base, "POST", f"/api/users/{student_id}/password", {"password": "newsmoke123"}, admin
    )
    check("resetear contraseña (200)", status == 200, f"status={status}")

    fresh = new_opener()
    status, relogin = request(
        base, "POST", "/api/auth/login", {"email": student_email, "password": "newsmoke123"}, fresh
    )
    check(
        "login con la contraseña reseteada (200)",
        status == 200 and isinstance(relogin, dict),
        f"status={status}",
    )

    status, _ = request(
        base, "POST", f"/api/users/{student_id}/password", {"password": "short"}, admin
    )
    check("resetear con contraseña corta (400)", status == 400, f"status={status}")

    # Deactivate and confirm the account can no longer authenticate.
    status, deactivated = request(
        base, "PATCH", f"/api/users/{student_id}", {"active": False}, admin
    )
    check(
        "desactivar usuario (200, active=false)",
        status == 200 and isinstance(deactivated, dict) and deactivated.get("active") is False,
        f"status={status}",
    )

    inactive = new_opener()
    status, _ = request(
        base, "POST", "/api/auth/login", {"email": student_email, "password": "newsmoke123"}, inactive
    )
    check("cuenta inactiva no puede iniciar sesión (401)", status == 401, f"status={status}")

    # Self-management is blocked.
    status, _ = request(base, "PATCH", f"/api/users/{admin_id}", {"active": False}, admin)
    check("autodesactivación bloqueada (400)", status == 400, f"status={status}")

    status, _ = request(
        base,
        "PUT",
        f"/api/users/{admin_id}",
        {
            "first_name": "Admin",
            "last_name": "Root",
            "email": admin_email,
            "role": "student",
        },
        admin,
    )
    check("autocambio de rol bloqueado (400)", status == 400, f"status={status}")

    status, _ = request(base, "PATCH", "/api/users/999999", {"active": False}, admin)
    check("operación sobre usuario inexistente (404)", status == 404, f"status={status}")

    # Remove the professor assignment.
    status, _ = request(
        base, "DELETE", f"/api/courses/{course_id}/teachers/{student_id}", opener=admin
    )
    check("quitar profesor del curso (200)", status == 200, f"status={status}")

    status, teachers = request(base, "GET", f"/api/courses/{course_id}/teachers", opener=admin)
    ids = [teacher.get("id") for teacher in teachers] if isinstance(teachers, list) else []
    check(
        "el profesor ya no figura en el curso",
        status == 200 and student_id not in ids,
        f"status={status} ids={ids}",
    )

    status, _ = request(
        base, "DELETE", f"/api/courses/{course_id}/teachers/{student_id}", opener=admin
    )
    check("quitar asignación inexistente (404)", status == 404, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-04: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
