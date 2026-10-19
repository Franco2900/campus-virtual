"""Portable end-to-end smoke test for the CU-11 (chatbot assistant) flow.

Exercises POST /api/chat/messages and GET /api/chat/messages: authorization
(401 without session), validation (400 for empty content), the happy path
(201 with an assistant reply when Ollama is up), the service-failure path
(502 with the friendly A7 error when Ollama is down), per-user history
isolation, and deleting the user's own history (CU-11 A9, idempotent).
Requires the backend (and Vite proxy) to be running;
`scripts/verify.py --cu cu11` handles that with an isolated database.

Usage:
    python scripts/smoke_cu11.py [--base http://127.0.0.1:5000]

Exit code is 0 when every step PASSes, 1 otherwise.
"""

import argparse
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request
import uuid


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
        response = opener.open(req, timeout=60)
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
    return request(
        base, "POST", "/api/auth/login", {"email": email, "password": password}, opener
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    anonymous = new_opener()
    student = new_opener()
    other = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # A1: anonymous access is rejected on both endpoints
    status, _ = request(
        base, "POST", "/api/chat/messages", {"content": "hola"}, opener=anonymous
    )
    check("consulta anónima sin sesión (401)", status == 401, f"status={status}")

    status, _ = request(base, "GET", "/api/chat/messages", opener=anonymous)
    check("historial sin sesión (401)", status == 401, f"status={status}")

    status, _ = request(base, "DELETE", "/api/chat/messages", opener=anonymous)
    check(
        "borrado de historial sin sesión (401)", status == 401, f"status={status}"
    )

    # Register + login the first user (Estudiante is enough; chat is open to all three roles)
    student_email, _, reg_status = register_user(base, student, "est")
    check("registro estudiante (201)", reg_status == 201, f"status={reg_status}")
    status, login_data = login(base, student, student_email)
    check(
        "login estudiante (200)",
        status == 200
        and isinstance(login_data, dict)
        and login_data.get("role") == "student",
        f"status={status}",
    )

    # Initial history: empty conversation
    status, history = request(base, "GET", "/api/chat/messages", opener=student)
    empty_ok = (
        status == 200
        and isinstance(history, dict)
        and isinstance(history.get("messages"), list)
        and history.get("messages") == []
    )
    check("historial inicial vacío (200)", empty_ok, f"status={status}")

    # Validation: empty content -> 400
    status, err = request(
        base, "POST", "/api/chat/messages", {"content": "   "}, opener=student
    )
    has_error = isinstance(err, dict) and "error" in err
    check(
        "consulta vacía (400, mensaje error)",
        status == 400 and has_error,
        f"status={status}",
    )

    # Happy path (Ollama up) or service failure (Ollama down)
    status, turn = request(
        base,
        "POST",
        "/api/chat/messages",
        {"content": "¿Qué cursos existen?"},
        opener=student,
    )
    ollama_up = status == 201
    if ollama_up:
        assistant = turn.get("assistant_message") if isinstance(turn, dict) else None
        user_msg = turn.get("user_message") if isinstance(turn, dict) else None
        check(
            "consulta válida (201, respuesta del asistente)",
            isinstance(assistant, dict)
            and assistant.get("role") == "assistant"
            and bool(assistant.get("content"))
            and isinstance(user_msg, dict),
            f"status={status}",
        )
    elif status == 502:
        friendly = isinstance(turn, dict) and "error" in turn
        check(
            "consulta con Ollama caído (502, error amable)",
            friendly,
            f"status={status}",
        )
        print("[SKIP] Ollama no disponible: se validó A7")
    else:
        check("consulta válida (201 o 502)", False, f"status={status} body={turn}")

    # History now includes the user message (only meaningful when the turn succeeded)
    status, history = request(base, "GET", "/api/chat/messages", opener=student)
    messages = history.get("messages", []) if isinstance(history, dict) else []
    roles = [m.get("role") for m in messages if isinstance(m, dict)]
    if ollama_up:
        check(
            "historial incluye user y assistant (200)",
            status == 200 and "user" in roles and "assistant" in roles,
            f"status={status} roles={roles}",
        )
    else:
        # D-D: on 502 the failed turn is not persisted; history may stay empty
        check(
            "historial sin turno fallido (200, no persistido en 502)",
            status == 200 and "user" not in roles,
            f"status={status} roles={roles}",
        )

    # History isolation: a second user starts with their own empty history
    other_email, _, _ = register_user(base, other, "otro")
    login(base, other, other_email)
    status, other_history = request(base, "GET", "/api/chat/messages", opener=other)
    other_messages = (
        other_history.get("messages", []) if isinstance(other_history, dict) else []
    )
    first_contents = {m.get("content") for m in messages if isinstance(m, dict)}
    leaked = any(
        m.get("content") in first_contents
        for m in other_messages
        if isinstance(m, dict)
    )
    check(
        "aislamiento de historial entre usuarios (200)",
        status == 200 and other_messages == [] and not leaked,
        f"status={status} count={len(other_messages)}",
    )

    # CU-11 extension (A9): the user deletes their own history; repeating it is safe
    status, _ = request(base, "DELETE", "/api/chat/messages", opener=student)
    check("eliminar el historial propio (200)", status == 200, f"status={status}")

    status, history = request(base, "GET", "/api/chat/messages", opener=student)
    remaining = history.get("messages", []) if isinstance(history, dict) else None
    check(
        "historial vacío después de eliminar (200, 0 mensajes)",
        status == 200 and remaining == [],
        f"status={status} count={len(remaining) if isinstance(remaining, list) else 'n/a'}",
    )

    status, _ = request(base, "DELETE", "/api/chat/messages", opener=student)
    check("eliminar sin historial (200, idempotente)", status == 200, f"status={status}")

    status, other_history = request(base, "GET", "/api/chat/messages", opener=other)
    check(
        "el borrado no afecta a otro usuario (200)",
        status == 200
        and isinstance(other_history, dict)
        and other_history.get("messages") == [],
        f"status={status}",
    )

    ok = all(results)
    print(f"\nCU-11 smoke: {sum(results)}/{len(results)} checks")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
