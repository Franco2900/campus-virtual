"""Portable end-to-end smoke test for the CU-02 (registration + auth) flow.

Requires the backend (and optionally the frontend proxy) to be running.
Uses only the standard library so it runs unchanged on Windows, Linux and macOS.

Usage:
    python scripts/smoke_cu02.py [--base http://127.0.0.1:5000]

Exit code is 0 when every step PASSes, 1 otherwise.
"""

import argparse
import http.cookiejar
import json
import sys
import uuid
import urllib.error
import urllib.request

INVALID_CREDENTIALS_MESSAGE = "El correo electrónico o la contraseña son incorrectos"


def request(base, method, path, body=None, opener=None):
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

    cookies = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    email = f"smoke-{uuid.uuid4()}@example.com"
    password = "smoke12345"

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    status, user = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "Smoke",
            "last_name": "Auth",
            "email": email,
            "password": password,
        },
        opener,
    )
    check(
        "registro exitoso (201)",
        status == 201 and user.get("role") == "student" and "password" not in user,
        f"status={status}",
    )

    status, body = request(base, "POST", "/api/auth/register", {
        "first_name": "X", "last_name": "Y", "email": email, "password": password
    }, opener)
    check("registro duplicado (409)", status == 409)

    status, login = request(
        base, "POST", "/api/auth/login", {"email": email, "password": password}, opener
    )
    check(
        "login correcto (200)",
        status == 200
        and login.get("email") == email
        and login.get("role") == "student"
        and "password" not in login,
        f"status={status}",
    )

    status, me = request(base, "GET", "/api/auth/me", opener=opener)
    check("me con sesión (200)", status == 200 and me.get("email") == email, f"status={status}")

    status, wrong = request(
        base, "POST", "/api/auth/login", {"email": email, "password": "incorrecta1"}, opener
    )
    check("login password incorrecto (401)", status == 401, f"status={status}")

    status, missing = request(
        base, "POST", "/api/auth/login", {"email": email}, opener
    )
    check("login sin contraseña (400)", status == 400, f"status={status}")

    status, unknown = request(
        base,
        "POST",
        "/api/auth/login",
        {"email": "nobody@example.com", "password": "whatever1"},
        opener,
    )
    check(
        "login correo inexistente (401, mismo mensaje)",
        status == 401
        and unknown.get("error") == INVALID_CREDENTIALS_MESSAGE
        and wrong.get("error") == INVALID_CREDENTIALS_MESSAGE,
        f"status={status}",
    )

    status, body = request(base, "POST", "/api/auth/logout", opener=opener)
    check("logout con sesión (200)", status == 200, f"status={status}")

    status, me_after = request(base, "GET", "/api/auth/me", opener=opener)
    check("me tras logout (401)", status == 401, f"status={status}")

    status, body = request(base, "POST", "/api/auth/logout", opener=opener)
    check("logout sin sesión (200, idempotente)", status == 200, f"status={status}")

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-02: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()