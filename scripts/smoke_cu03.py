"""Portable end-to-end smoke test for the CU-03 (course management) flow.

Requires the backend (and the Vite proxy) to be running with the admin already
seeded; `scripts/verify.py --cu cu03` handles that with an isolated database.
Reads the admin credentials from CAMPUS_ADMIN_EMAIL / CAMPUS_ADMIN_PASSWORD,
falling back to the same smoke defaults used by verify.py.

Usage:
    python scripts/smoke_cu03.py [--base http://127.0.0.1:5000]

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
    status, _ = request(base, "GET", "/api/courses", opener=anonymous)
    check("listar cursos sin sesión (401)", status == 401, f"status={status}")

    status, _ = request(base, "POST", "/api/courses", {"name": "X", "code": "X1"}, anonymous)
    check("crear curso sin sesión (401)", status == 401, f"status={status}")

    # A student is authenticated but not authorized.
    student_email = f"smoke-student-{uuid.uuid4()}@example.com"
    request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "Smoke",
            "last_name": "Student",
            "email": student_email,
            "password": "smoke12345",
        },
        student,
    )
    request(
        base,
        "POST",
        "/api/auth/login",
        {"email": student_email, "password": "smoke12345"},
        student,
    )
    status, _ = request(base, "GET", "/api/courses", opener=student)
    check("estudiante no autorizado (403)", status == 403, f"status={status}")

    # Admin login.
    status, login = request(
        base,
        "POST",
        "/api/auth/login",
        {"email": admin_email, "password": admin_password},
        admin,
    )
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login, dict) and login.get("role") == "admin",
        f"status={status}",
    )

    # Seeded demo courses (mix of active and inactive).
    status, courses = request(base, "GET", "/api/courses", opener=admin)
    ok = status == 200 and isinstance(courses, list) and len(courses) >= 4
    has_active = any(course.get("active") for course in courses) if ok else False
    has_inactive = any(not course.get("active") for course in courses) if ok else False
    check(
        "listar cursos sembrados (200, activos e inactivos)",
        ok and has_active and has_inactive,
        f"status={status} count={len(courses) if isinstance(courses, list) else 'n/a'}",
    )

    # Create + duplicate + validation.
    code = f"SMK{uuid.uuid4().hex[:6].upper()}"
    status, created = request(
        base,
        "POST",
        "/api/courses",
        {"name": "Smoke Course", "code": code, "description": "smoke"},
        admin,
    )
    check(
        "alta de curso (201)",
        status == 201 and isinstance(created, dict) and created.get("code") == code,
        f"status={status}",
    )

    status, _ = request(
        base, "POST", "/api/courses", {"name": "Otra", "code": code.lower()}, admin
    )
    check("código duplicado case-insensitive (409)", status == 409, f"status={status}")

    status, _ = request(
        base, "POST", "/api/courses", {"description": "sin nombre ni código"}, admin
    )
    check("alta con faltantes (400)", status == 400, f"status={status}")

    course_id = created.get("id") if isinstance(created, dict) else None

    # Read, update, toggle, missing.
    status, fetched = request(base, "GET", f"/api/courses/{course_id}", opener=admin)
    check(
        "obtener curso por id (200)",
        status == 200 and isinstance(fetched, dict) and fetched.get("id") == course_id,
        f"status={status}",
    )

    status, updated = request(
        base,
        "PUT",
        f"/api/courses/{course_id}",
        {"name": "Smoke Course v2", "code": code},
        admin,
    )
    check(
        "editar curso (200)",
        status == 200 and isinstance(updated, dict) and updated.get("name") == "Smoke Course v2",
        f"status={status}",
    )

    status, patched = request(
        base, "PATCH", f"/api/courses/{course_id}", {"active": False}, admin
    )
    check(
        "desactivar curso (200, active=false)",
        status == 200 and isinstance(patched, dict) and patched.get("active") is False,
        f"status={status}",
    )

    status, patched = request(
        base, "PATCH", f"/api/courses/{course_id}", {"active": True}, admin
    )
    check(
        "reactivar curso (200, active=true)",
        status == 200 and isinstance(patched, dict) and patched.get("active") is True,
        f"status={status}",
    )

    status, _ = request(base, "GET", "/api/courses/999999", opener=admin)
    check("curso inexistente (404)", status == 404, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-03: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
