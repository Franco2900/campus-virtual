"""Smoke test para CU-01 (Registrarse).

Requiere el backend (y opcionalmente el frontend proxy) en ejecución.
Usa solo la biblioteca estándar, sin dependencias nuevas.

Uso:
    python scripts/smoke_cu01.py [--base http://127.0.0.1:5000]

Código de salida 0 si todos los checks PASS, 1 si alguno falla.
"""

import argparse
import http.cookiejar
import json
import sys
import uuid
import urllib.error
import urllib.request


def request(base, method, path, body=None, opener=None):
    url = base + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        response = opener.open(req, timeout=10) if opener is not None else urllib.request.urlopen(req, timeout=10)
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
            "last_name": "Cu01",
            "email": email,
            "password": password,
        },
        opener,
    )
    check(
        "alta válida (201)",
        status == 201 and isinstance(user, dict) and user.get("role") == "student" and "password" not in user and "password_hash" not in user,
        f"status={status}",
    )

    status, body_dup = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "X",
            "last_name": "Y",
            "email": email,
            "password": password,
        },
        opener,
    )
    check("mismo email repetido (409)", status == 409, f"status={status}")

    status, body_bad_email = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "A",
            "last_name": "B",
            "email": "not-an-email",
            "password": password,
        },
        opener,
    )
    check("email con formato inválido (400)", status == 400, f"status={status}")

    status, body_short = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "A",
            "last_name": "B",
            "email": f"smoke-{uuid.uuid4()}@example.com",
            "password": "short",
        },
        opener,
    )
    check("contraseña de menos de 8 caracteres (400)", status == 400, f"status={status}")

    email2 = f"smoke-{uuid.uuid4()}@example.com"
    status, user2 = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "C",
            "last_name": "D",
            "email": email2,
            "password": password,
            "role": "admin",
        },
        opener,
    )
    check(
        'payload con "role": "admin" se ignora (201, queda student)',
        status == 201 and isinstance(user2, dict) and user2.get("role") == "student",
        f"status={status}",
    )

    status, me_after_reg = request(base, "GET", "/api/auth/me", opener=opener)
    check("registro no abre sesion (GET /api/auth/me -> 401)", status == 401, f"status={status}")

    status, login_res = request(
        base,
        "POST",
        "/api/auth/login",
        {"email": email, "password": password},
        opener,
    )
    check(
        "login con la cuenta recién creada (200)",
        status == 200 and isinstance(login_res, dict) and login_res.get("email") == email and login_res.get("role") == "student" and "password" not in login_res,
        f"status={status}",
    )

    failed = sum(1 for result in results if not result)
    total = len(results)
    print(f"\nSmoke CU-01: {total - failed}/{total} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
