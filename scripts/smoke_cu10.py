"""Portable end-to-end smoke test for the CU-10 (filter users) flow.

Exercises GET /api/users filtering with query params q, role, active (combined
with AND), validates error cases (400 for invalid role/active), and verifies
authorization (401 without session, 403 for non-admin). Requires the backend
(and Vite proxy) to be running with admin seeded; `scripts/verify.py --cu cu10`
handles that with an isolated database.

Usage:
    python scripts/smoke_cu10.py [--base http://127.0.0.1:5000]

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


def register_user(base, opener, label, first_name="Smoke", last_name=None):
    if last_name is None:
        last_name = label.title()
    email = f"smoke-{label}-{uuid.uuid4()}@example.com"
    status, user = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": first_name,
            "last_name": last_name,
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
    teacher = new_opener()
    admin = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # Anonymous access without filters - 401
    status, _ = request(base, "GET", "/api/users", opener=anonymous)
    check("listar usuarios sin sesión (401)", status == 401, f"status={status}")

    # Anonymous access with filters - 401
    status, _ = request(base, "GET", "/api/users?q=ana", opener=anonymous)
    check("filtrar usuarios sin sesión (401)", status == 401, f"status={status}")

    # Student access without filters - 403
    student_email, _, _ = register_user(base, student, "est", first_name="Ana", last_name="Lopez")
    login(base, student, student_email)
    status, _ = request(base, "GET", "/api/users", opener=student)
    check("estudiante no autorizado (403)", status == 403, f"status={status}")

    # Student access with filters - 403
    status, _ = request(base, "GET", "/api/users?role=student", opener=student)
    check("estudiante no autorizado con filtros (403)", status == 403, f"status={status}")

    # Teacher access without filters - 403
    teacher_email, teacher_id, _ = register_user(base, teacher, "prof", first_name="Carlos", last_name="Mendez")
    login(base, teacher, teacher_email)
    status, _ = request(base, "GET", "/api/users", opener=teacher)
    check("profesor no autorizado (403)", status == 403, f"status={status}")

    # Teacher access with filters - 403
    status, _ = request(base, "GET", "/api/users?role=teacher", opener=teacher)
    check("profesor no autorizado con filtros (403)", status == 403, f"status={status}")

    # Admin login
    status, login_data = request(
        base, "POST", "/api/auth/login", {"email": admin_email, "password": admin_password}, admin
    )
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login_data, dict) and login_data.get("role") == "admin",
        f"status={status}",
    )

    # List without criteria - returns all users (compatibility)
    status, all_users = request(base, "GET", "/api/users", opener=admin)
    all_users_list = all_users if isinstance(all_users, list) else []
    check(
        "listar sin criterios (200)",
        status == 200 and isinstance(all_users, list),
        f"status={status} count={len(all_users_list)}",
    )

    # q partial case-insensitive search on name/last/email
    status, q_results = request(base, "GET", "/api/users?q=ana", opener=admin)
    q_list = q_results if isinstance(q_results, list) else []
    has_ana = any("ana" in (u.get("first_name", "").lower()) or "ana" in (u.get("last_name", "").lower()) or "ana" in (u.get("email", "").lower()) for u in q_list)
    check(
        "filtro q=ana case-insensitive (200 + resultados)",
        status == 200 and has_ana,
        f"status={status} count={len(q_list)}",
    )

    # q with spaces (blank) should be treated as no criteria - returns full list
    status, q_blank = request(base, "GET", "/api/users?q=%20%20", opener=admin)
    check(
        "filtro q en blanco = sin criterio (200)",
        status == 200 and isinstance(q_blank, list) and len(q_blank) == len(all_users_list),
        f"status={status} count={len(q_blank) if isinstance(q_blank, list) else 'n/a'}",
    )

    # filter by role=student
    status, role_student = request(base, "GET", "/api/users?role=student", opener=admin)
    role_student_list = role_student if isinstance(role_student, list) else []
    all_student = all(r.get("role") == "student" for r in role_student_list)
    check(
        "filtro role=student (200)",
        status == 200 and all_student and len(role_student_list) >= 1,
        f"status={status} count={len(role_student_list)}",
    )

    # filter by role=teacher
    status, role_teacher = request(base, "GET", "/api/users?role=teacher", opener=admin)
    role_teacher_list = role_teacher if isinstance(role_teacher, list) else []
    all_teacher = all(r.get("role") == "teacher" for r in role_teacher_list)
    check(
        "filtro role=teacher (200)",
        status == 200 and all_teacher,
        f"status={status} count={len(role_teacher_list)}",
    )

    # filter by role=admin
    status, role_admin = request(base, "GET", "/api/users?role=admin", opener=admin)
    role_admin_list = role_admin if isinstance(role_admin, list) else []
    all_admin = all(r.get("role") == "admin" for r in role_admin_list)
    check(
        "filtro role=admin (200)",
        status == 200 and all_admin and len(role_admin_list) >= 1,
        f"status={status} count={len(role_admin_list)}",
    )

    # filter by active=true
    status, active_true = request(base, "GET", "/api/users?active=true", opener=admin)
    active_true_list = active_true if isinstance(active_true, list) else []
    all_active = all(r.get("active") is True for r in active_true_list)
    check(
        "filtro active=true (200)",
        status == 200 and all_active,
        f"status={status} count={len(active_true_list)}",
    )

    # filter by active=false (we created Ana as student who is active by default; but we can also create inactive)
    status, active_false = request(base, "GET", "/api/users?active=false", opener=admin)
    active_false_list = active_false if isinstance(active_false, list) else []
    all_inactive = all(r.get("active") is False for r in active_false_list)
    check(
        "filtro active=false (200)",
        status == 200 and all_inactive,
        f"status={status} count={len(active_false_list)}",
    )

    # combined AND: q + role
    status, combined_q_role = request(base, "GET", "/api/users?q=ana&role=student", opener=admin)
    combined_q_role_list = combined_q_role if isinstance(combined_q_role, list) else []
    ok_combined1 = all(
        ("ana" in (u.get("first_name", "").lower()) or "ana" in (u.get("last_name", "").lower()) or "ana" in (u.get("email", "").lower())) and u.get("role") == "student"
        for u in combined_q_role_list
    )
    check(
        "filtros combinados q+role (200, AND)",
        status == 200 and ok_combined1,
        f"status={status} count={len(combined_q_role_list)}",
    )

    # combined AND: role + active
    status, combined_role_active = request(base, "GET", "/api/users?role=student&active=true", opener=admin)
    combined_role_active_list = combined_role_active if isinstance(combined_role_active, list) else []
    ok_combined2 = all(u.get("role") == "student" and u.get("active") is True for u in combined_role_active_list)
    check(
        "filtros combinados role+active (200, AND)",
        status == 200 and ok_combined2,
        f"status={status} count={len(combined_role_active_list)}",
    )

    # combined AND: q + role + active
    status, combined_all = request(base, "GET", "/api/users?q=ana&role=student&active=true", opener=admin)
    combined_all_list = combined_all if isinstance(combined_all, list) else []
    ok_combined3 = all(
        ("ana" in (u.get("first_name", "").lower()) or "ana" in (u.get("last_name", "").lower()) or "ana" in (u.get("email", "").lower())) and u.get("role") == "student" and u.get("active") is True
        for u in combined_all_list
    )
    check(
        "filtros combinados q+role+active (200, AND)",
        status == 200 and ok_combined3,
        f"status={status} count={len(combined_all_list)}",
    )

    # invalid role - 400 with error
    status, err_role = request(base, "GET", "/api/users?role=superuser", opener=admin)
    has_error_role = isinstance(err_role, dict) and "error" in err_role
    check(
        "role inválido (400, mensaje error)",
        status == 400 and has_error_role,
        f"status={status} body={err_role}",
    )

    # invalid active - 400 with error
    status, err_active = request(base, "GET", "/api/users?active=maybe", opener=admin)
    has_error_active = isinstance(err_active, dict) and "error" in err_active
    check(
        "active inválido (400, mensaje error)",
        status == 400 and has_error_active,
        f"status={status} body={err_active}",
    )

    # invalid criterion takes precedence over valid - 400
    status, err_combo = request(base, "GET", "/api/users?q=ana&role=invalido", opener=admin)
    has_error_combo = isinstance(err_combo, dict) and "error" in err_combo
    check(
        "criterio inválido prevalece (400)",
        status == 400 and has_error_combo,
        f"status={status} body={err_combo}",
    )

    # Also check active without value case conceptually - but HTTP query param might come as empty; service validates
    status, err_active_empty = request(base, "GET", "/api/users?active=", opener=admin)
    has_error_active_empty = isinstance(err_active_empty, dict) and "error" in err_active_empty
    check(
        "active vacío (400)",
        status == 400 and has_error_active_empty,
        f"status={status}",
    )

    ok = all(results)
    print(f"\nCU-10 smoke: {sum(results)}/{len(results)} checks")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
