"""Portable end-to-end smoke test for the CU-12 (chatbot knowledge sources) flow.

Exercises GET/POST/DELETE /api/knowledge/sources: authorization (401 without
session, 403 for a non-admin user), server-side validation of the upload
(rejected extension creates no row), the happy path (201 with the source
ingested, then polled until `active`), a chat consultation answered with the
newly indexed source, deletion (200), absence from the listing afterwards
(A7) and a second delete of the same id (404).

Requires the backend (and Vite proxy) to be running; `scripts/verify.py --cu
cu12` handles that with an isolated database. Indexing also requires a local
Ollama server with the `nomic-embed-text` embedding model: when it is not
available the upload fails with 400 and an `error` row is persisted (A5), the
201 check FAILS, and the poll/chat checks print an explicit `[SKIP]` line and
are not counted. Expected totals: 18 checks with Ollama up, 16 with Ollama
down (1 FAIL on the 201 upload, 15 PASS, 2 SKIP lines).

Usage:
    python scripts/smoke_cu12.py [--base http://127.0.0.1:5000]

Exit code is 0 when every step PASSes, 1 otherwise.
"""

import argparse
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

DEFAULT_ADMIN_EMAIL = "admin@smoke.test"
DEFAULT_ADMIN_PASSWORD = "smoke-admin-123"

TEST_TOKEN = "zancudolosis"
TEST_MD = (
    "# Guía de prueba CU-12\n\n"
    f"{TEST_TOKEN} es un término de prueba exclusivo del Campus Virtual.\n"
)
POLL_ATTEMPTS = 30
POLL_DELAY_SECONDS = 1


def new_opener():
    cookies = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))


def parse_response(response):
    raw = response.read().decode("utf-8")
    try:
        payload = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        payload = raw
    return response.status, payload


def request(base, method, path, body=None, opener=None, timeout=60):
    if opener is None:
        opener = urllib.request.build_opener()
    url = base + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        response = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    return parse_response(response)


def build_multipart(fields, file_field, filename, content, content_type="text/markdown"):
    boundary = uuid.uuid4().hex
    parts = []
    for key, values in fields.items():
        for value in values:
            parts.append(f"--{boundary}\r\n")
            parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n')
            parts.append(f"{value}\r\n")
    parts.append(f"--{boundary}\r\n")
    parts.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n')
    parts.append(f"Content-Type: {content_type}\r\n\r\n")
    head = "".join(parts).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return head + content + tail, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def upload_source(
    base, opener, fields, filename, content, content_type="text/markdown", timeout=180
):
    data, headers = build_multipart(fields, "file", filename, content, content_type)
    url = base + "/api/knowledge/sources"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        response = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    return parse_response(response)


def login(base, opener, email, password):
    return request(base, "POST", "/api/auth/login", {"email": email, "password": password}, opener)


def list_sources(base, opener):
    status, payload = request(base, "GET", "/api/knowledge/sources", opener=opener)
    sources = payload.get("sources") if isinstance(payload, dict) else None
    if not isinstance(sources, list):
        sources = []
    return status, sources


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

    # Authorization: anonymous access is rejected on every endpoint (401)
    status, _ = request(base, "GET", "/api/knowledge/sources", opener=anonymous)
    check("listado sin sesión (401)", status == 401, f"status={status}")

    status, _ = request(base, "POST", "/api/knowledge/sources", opener=anonymous)
    check("alta sin sesión (401)", status == 401, f"status={status}")

    status, _ = request(base, "DELETE", "/api/knowledge/sources/1", opener=anonymous)
    check("borrado sin sesión (401)", status == 401, f"status={status}")

    # Non-admin user: management endpoints answer 403 (A3)
    email = f"smoke-cu12-{uuid.uuid4()}@example.com"
    status, user = request(
        base,
        "POST",
        "/api/auth/register",
        {
            "first_name": "Smoke",
            "last_name": "Cu12",
            "email": email,
            "password": "smoke12345",
        },
        student,
    )
    check("registro estudiante (201)", status == 201, f"status={status}")
    status, login_data = login(base, student, email, "smoke12345")
    check(
        "login estudiante (200, role student)",
        status == 200 and isinstance(login_data, dict) and login_data.get("role") == "student",
        f"status={status}",
    )

    status, _ = request(base, "GET", "/api/knowledge/sources", opener=student)
    check("listado como estudiante (403)", status == 403, f"status={status}")

    status, _ = request(base, "POST", "/api/knowledge/sources", opener=student)
    check("alta como estudiante (403)", status == 403, f"status={status}")

    status, _ = request(base, "DELETE", "/api/knowledge/sources/1", opener=student)
    check("borrado como estudiante (403)", status == 403, f"status={status}")

    # Admin session
    status, login_data = login(base, admin, admin_email, admin_password)
    check(
        "login admin (200, role admin)",
        status == 200 and isinstance(login_data, dict) and login_data.get("role") == "admin",
        f"status={status}",
    )

    status, sources = list_sources(base, admin)
    check(
        "listado admin (200, lista de fuentes)",
        status == 200 and isinstance(sources, list),
        f"status={status}",
    )
    count_before = len(sources)

    # Server-side validation: a rejected extension returns 400 and creates no row (A4)
    status, body = upload_source(
        base,
        admin,
        {
            "name": ["Fuente inválida smoke"],
            "description": [""],
            "source_type": ["document"],
        },
        "malware.exe",
        b"not-an-allowed-file",
        content_type="application/octet-stream",
    )
    check(
        "extensión no admitida (400 con error)",
        status == 400 and isinstance(body, dict) and bool(body.get("error")),
        f"status={status}",
    )

    status, sources = list_sources(base, admin)
    check(
        "la validación no crea fila (listado sin cambios)",
        status == 200 and len(sources) == count_before,
        f"status={status} antes={count_before} después={len(sources)}",
    )

    # Happy path: upload a .md with a distinctive token and ingest it (needs Ollama)
    source_name = f"Guía smoke CU-12 {uuid.uuid4().hex[:8]}"
    status, body = upload_source(
        base,
        admin,
        {
            "name": [source_name],
            "description": ["Término de prueba para el smoke del CU-12"],
            "source_type": ["document"],
            "target_roles": ["student", "teacher", "admin"],
        },
        "guia-smoke-cu12.md",
        TEST_MD.encode("utf-8"),
    )

    source_id = None
    indexed = False
    if status == 201 and isinstance(body, dict) and isinstance(body.get("source"), dict):
        source_id = body["source"].get("id")
        check("alta de fuente válida (201, procesada)", True, f"id={source_id}")
        indexed = True
    else:
        # 400 here means the ingestion failed (Ollama down or nomic-embed-text
        # missing): the service persists an `error` row as compensation (A5).
        check(
            "alta de fuente válida (201, procesada)",
            False,
            f"status={status} body={body} — ¿Ollama caído o sin nomic-embed-text?",
        )
        status, sources = list_sources(base, admin)
        row = next((item for item in sources if item.get("name") == source_name), None)
        if row is None:
            check(
                "fila en error persistida tras el fallo (A5)",
                False,
                "no se encontró la fila en el listado",
            )
        else:
            source_id = row.get("id")
            check(
                "fila en error persistida tras el fallo (A5)",
                row.get("status") == "error" and bool(row.get("error_message")),
                f"status={row.get('status')}",
            )

    # Poll the listing until the source reaches `active`
    if indexed:
        active = False
        for _ in range(POLL_ATTEMPTS):
            status, sources = list_sources(base, admin)
            row = next((item for item in sources if item.get("id") == source_id), None)
            if row is not None and row.get("status") == "active":
                active = True
                break
            time.sleep(POLL_DELAY_SECONDS)
        check(
            "fuente en active tras el indexado (poll GET)",
            active,
            f"id={source_id}",
        )
    else:
        print("[SKIP] fuente no indexada (Ollama sin nomic-embed-text): sin poll de estado")

    # Chat consultation backed by the new source (skipped when not indexed)
    if indexed:
        status, turn = request(
            base,
            "POST",
            "/api/chat/messages",
            {"content": f"¿Qué es {TEST_TOKEN}?"},
            student,
            timeout=150,
        )
        if status == 201:
            assistant = turn.get("assistant_message") if isinstance(turn, dict) else None
            check(
                "consulta al chat con la fuente cargada (201, respuesta)",
                isinstance(assistant, dict) and bool(assistant.get("content")),
                f"status={status}",
            )
        elif status == 502:
            print("[SKIP] Ollama no disponible para el turno de chat: consulta no contada")
        else:
            check("consulta al chat con la fuente cargada (201 o 502)", False, f"status={status}")
    else:
        print("[SKIP] fuente no indexada: sin consulta al chat")

    # Deletion and absence from the listing (A7)
    if source_id is None:
        check("borrado de la fuente (200)", False, "sin fila para probar el borrado")
        check("fuente ausente del listado tras borrar (A7)", False, "sin fila para probar el borrado")
        check("borrado repetido de la misma fuente (404)", False, "sin fila para probar el borrado")
    else:
        status, body = request(base, "DELETE", f"/api/knowledge/sources/{source_id}", opener=admin)
        check("borrado de la fuente (200)", status == 200, f"status={status}")

        status, sources = list_sources(base, admin)
        present = any(item.get("id") == source_id for item in sources)
        check(
            "fuente ausente del listado tras borrar (A7)",
            status == 200 and not present,
            f"status={status} presente={present}",
        )

        status, body = request(base, "DELETE", f"/api/knowledge/sources/{source_id}", opener=admin)
        check("borrado repetido de la misma fuente (404)", status == 404, f"status={status}")

    ok = all(results)
    print(f"\nCU-12 smoke: {sum(results)}/{len(results)} checks")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
