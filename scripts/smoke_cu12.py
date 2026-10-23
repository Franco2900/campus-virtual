"""Portable end-to-end smoke test for the CU-12 (knowledge sources) flow.

Exercises GET/POST/DELETE /api/knowledge/sources: authorization (401 without
session, 403 for a non-Administrador role), validation (400 for an unsupported
extension, 400 for a file over 1 MB, 400 for a missing name, 400 for an invalid
source type), the happy path (201 with the serialized source, indexed and
active), listing the created source, and deleting it (200, then 404 once it no
longer exists).
Requires the backend (and the Vite proxy) to be running;
`scripts/verify.py --cu cu12` handles that with an isolated database.

Usage:
    python scripts/smoke_cu12.py [--base http://127.0.0.1:5000]

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


def build_multipart(fields, files):
    boundary = f"----smoke{uuid.uuid4().hex}"
    parts = []
    for key, value in fields.items():
        if value is None:
            continue
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )
    for key, (filename, content, content_type) in files.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; '
            f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode("utf-8")
        )
        parts.append(content)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def multipart_request(base, path, fields, files, opener=None):
    if opener is None:
        opener = urllib.request.build_opener()
    body, content_type = build_multipart(fields, files)
    req = urllib.request.Request(
        base + path, data=body, headers={"Accept": "application/json"}, method="POST"
    )
    req.add_header("Content-Type", content_type)
    try:
        response = opener.open(req, timeout=120)
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
    status, _ = request(
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
    return email, status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    anonymous = new_opener()
    student = new_opener()
    admin = new_opener()

    results = []

    def check(name, condition, detail=""):
        label = "PASS" if condition else "FAIL"
        results.append(condition)
        suffix = f" — {detail}" if detail else ""
        print(f"[{label}] {name}{suffix}")

    # A1: anonymous access is rejected on every endpoint
    status, _ = request(base, "GET", "/api/knowledge/sources", opener=anonymous)
    check("listado sin sesión (401)", status == 401, f"status={status}")

    status, _ = multipart_request(
        base,
        "/api/knowledge/sources",
        {"name": "Anónimo", "source_type": "document"},
        {"file": ("anon.md", b"# anon\n", "text/markdown")},
        opener=anonymous,
    )
    check("carga sin sesión (401)", status == 401, f"status={status}")

    status, _ = request(base, "DELETE", "/api/knowledge/sources/1", opener=anonymous)
    check("borrado sin sesión (401)", status == 401, f"status={status}")

    # A2: a non-Administrador role is forbidden (403)
    student_email, reg_status = register_user(base, student, "est")
    check("registro estudiante (201)", reg_status == 201, f"status={reg_status}")
    status, login_data = request(
        base,
        "POST",
        "/api/auth/login",
        {"email": student_email, "password": "smoke12345"},
        opener=student,
    )
    check(
        "login estudiante (200)",
        status == 200
        and isinstance(login_data, dict)
        and login_data.get("role") == "student",
        f"status={status}",
    )

    status, _ = request(base, "GET", "/api/knowledge/sources", opener=student)
    check("listado como estudiante (403)", status == 403, f"status={status}")

    status, _ = multipart_request(
        base,
        "/api/knowledge/sources",
        {"name": "Estudiante", "source_type": "document"},
        {"file": ("est.md", b"# est\n", "text/markdown")},
        opener=student,
    )
    check("carga como estudiante (403)", status == 403, f"status={status}")

    status, _ = request(base, "DELETE", "/api/knowledge/sources/1", opener=student)
    check("borrado como estudiante (403)", status == 403, f"status={status}")

    # A3: the Administrador session drives the happy path
    status, login_data = request(
        base,
        "POST",
        "/api/auth/login",
        {"email": "admin@smoke.test", "password": "smoke-admin-123"},
        opener=admin,
    )
    check(
        "login administrador (200)",
        status == 200
        and isinstance(login_data, dict)
        and login_data.get("role") == "admin",
        f"status={status}",
    )

    status, listing = request(base, "GET", "/api/knowledge/sources", opener=admin)
    initial_count = 0
    if status == 200 and isinstance(listing, dict) and isinstance(listing.get("sources"), list):
        initial_count = len(listing["sources"])
    check(
        "listado como administrador (200, {sources: [...]})",
        status == 200 and isinstance(listing, dict) and isinstance(listing.get("sources"), list),
        f"status={status} count={initial_count}",
    )

    # A4: validation — unsupported extension, oversized file, missing name, invalid type
    status, payload = multipart_request(
        base,
        "/api/knowledge/sources",
        {"name": "Formato inválido", "source_type": "document"},
        {"file": ("invalido.pdf", b"%PDF-1.4\n", "application/pdf")},
        opener=admin,
    )
    check(
        "extensión no admitida (400, mensaje error)",
        status == 400 and isinstance(payload, dict) and bool(payload.get("error")),
        f"status={status}",
    )

    status, payload = multipart_request(
        base,
        "/api/knowledge/sources",
        {"name": "Demasiado grande", "source_type": "document"},
        {"file": ("grande.md", b"# grande\n" + b"x" * 1_100_000, "text/markdown")},
        opener=admin,
    )
    check(
        "archivo mayor a 1 MB (400, mensaje error)",
        status == 400 and isinstance(payload, dict) and bool(payload.get("error")),
        f"status={status}",
    )

    status, payload = multipart_request(
        base,
        "/api/knowledge/sources",
        {"source_type": "document"},
        {"file": ("sin-nombre.md", b"# sin nombre\n", "text/markdown")},
        opener=admin,
    )
    check(
        "nombre ausente (400, mensaje error)",
        status == 400 and isinstance(payload, dict) and bool(payload.get("error")),
        f"status={status}",
    )

    status, payload = multipart_request(
        base,
        "/api/knowledge/sources",
        {"name": "Tipo inválido", "source_type": "invalido"},
        {"file": ("tipo.md", b"# tipo\n", "text/markdown")},
        opener=admin,
    )
    check(
        "tipo de fuente inválido (400, mensaje error)",
        status == 400 and isinstance(payload, dict) and bool(payload.get("error")),
        f"status={status}",
    )

    # A5: happy path — a valid .md is indexed and returned active
    document = (
        b"# Politica academica\n\n## Entregas\n\n"
        b"Las entregas se realizan antes de la fecha limite del curso.\n"
    )
    status, created = multipart_request(
        base,
        "/api/knowledge/sources",
        {
            "name": "Fuente de prueba CU-12",
            "description": "Documento de prueba para el smoke CU-12",
            "source_type": "document",
            "target_roles": "student",
        },
        {"file": ("fuente_cu12.md", document, "text/markdown")},
        opener=admin,
    )
    source = created.get("source") if isinstance(created, dict) else None
    source_id = source.get("id") if isinstance(source, dict) else None
    check(
        "carga válida (201, fuente activa)",
        status == 201
        and isinstance(source, dict)
        and source_id is not None
        and source.get("status") == "active"
        and source.get("source_type") == "document"
        and source.get("target_roles") == ["student"]
        and isinstance(source.get("chunk_count"), int)
        and source.get("chunk_count") > 0,
        f"status={status} source={source}",
    )

    status, listing = request(base, "GET", "/api/knowledge/sources", opener=admin)
    sources = listing.get("sources", []) if isinstance(listing, dict) else []
    found = any(item.get("id") == source_id for item in sources)
    check(
        "la fuente creada aparece en el listado (200)",
        status == 200 and found and len(sources) == initial_count + 1,
        f"status={status} count={len(sources)}",
    )

    # A6: delete removes the row and the file; deleting again answers 404
    status, payload = request(
        base, "DELETE", f"/api/knowledge/sources/{source_id}", opener=admin
    )
    check(
        "borrado de la fuente (200, mensaje de confirmación)",
        status == 200 and isinstance(payload, dict) and bool(payload.get("message")),
        f"status={status}",
    )

    status, listing = request(base, "GET", "/api/knowledge/sources", opener=admin)
    sources = listing.get("sources", []) if isinstance(listing, dict) else []
    still_there = any(item.get("id") == source_id for item in sources)
    check(
        "la fuente ya no aparece en el listado (200)",
        status == 200 and not still_there and len(sources) == initial_count,
        f"status={status} count={len(sources)}",
    )

    status, payload = request(
        base, "DELETE", f"/api/knowledge/sources/{source_id}", opener=admin
    )
    check(
        "borrado de una fuente inexistente (404)",
        status == 404 and isinstance(payload, dict) and bool(payload.get("error")),
        f"status={status}",
    )

    ok = all(results)
    print(f"\nCU-12 smoke: {sum(results)}/{len(results)} checks")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
