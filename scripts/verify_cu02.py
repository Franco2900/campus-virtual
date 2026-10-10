"""Portable end-to-end verifier for CU-02 (registration + auth flow).

Starts backend and Vite, waits for readiness, runs the HTTP smoke against the
Vite proxy, and guarantees cleanup of every process tree it starts. Aborts
with a clear message if the ports are already taken, so orphan services never
accumulate.

Usage:
    python scripts/verify_cu02.py            # run and clean up
    python scripts/verify_cu02.py --keep     # leave backend and Vite running (.cu02-pids)
    python scripts/verify_cu02.py --cleanup  # stop services recorded by --keep

Exit code is 0 when every step PASSes, 1 when a step FAILs, 2 on abort.
"""

import argparse
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SMOKE_SCRIPT = PROJECT_ROOT / "scripts" / "smoke_cu02.py"
PIDS_FILE = PROJECT_ROOT / "scripts" / ".cu02-pids"
BASE_URL = "http://127.0.0.1:5173"
BACKEND_HEALTH_URL = "http://127.0.0.1:5000/api/auth/me"
TIMEOUT_SECONDS = 60


def port_is_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for(check, timeout, step_name, interval=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            print(f"[OK] {step_name}")
            return True
        time.sleep(interval)
    print(f"[FAIL] {step_name} (timeout {timeout}s)")
    return False


def backend_ready():
    try:
        urllib.request.urlopen(BACKEND_HEALTH_URL, timeout=2).read()
        return True
    except urllib.error.HTTPError:
        return True
    except OSError:
        return False


def frontend_ready():
    try:
        response = urllib.request.urlopen("http://127.0.0.1:5173", timeout=2)
        return response.status == 200
    except OSError:
        return False


def npm_command():
    return "npm.cmd" if sys.platform == "win32" else "npm"


def kill_process_tree(pid):
    if pid is None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def stop_recorded_services():
    if not PIDS_FILE.exists():
        print("[CLEANUP] No hay .cu02-pids; nada que detener.")
        return True
    ok = True
    for line in PIDS_FILE.read_text(encoding="utf-8").splitlines():
        pid = line.strip()
        if not pid.isdigit():
            continue
        kill_process_tree(int(pid))
        print(f"[CLEANUP] Terminado PID {pid}")
    PIDS_FILE.unlink(missing_ok=True)
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true", help="dejar backend y Vite corriendo")
    parser.add_argument("--cleanup", action="store_true", help="detener servicios registrados")
    args = parser.parse_args()

    if args.cleanup:
        stop_recorded_services()
        return 0

    print("Verificando puertos libres (pre-condicion anti-duplicados)...")
    if port_is_open("127.0.0.1", 5000) or port_is_open("127.0.0.1", 5173):
        print("[ABORT] Los puertos 5000/5173 estan ocupados. `python scripts/verify_cu02.py --cleanup` y reintente.")
        return 2

    backend_log = tempfile.NamedTemporaryFile(
        prefix="cu02-backend-", suffix=".log", delete=False
    ).name
    frontend_log = tempfile.NamedTemporaryFile(
        prefix="cu02-frontend-", suffix=".log", delete=False
    ).name

    backend_proc = None
    frontend_proc = None
    try:
        backend_log_handle = open(backend_log, "w")
        backend_proc = subprocess.Popen(
            [sys.executable, "run_backend.py"],
            cwd=str(BACKEND_DIR),
            stdout=backend_log_handle,
            stderr=backend_log_handle,
            start_new_session=os.name != "nt",
        )
        backend_log_handle.close()
        print(f"[OK] Backend iniciado (pid {backend_proc.pid})")

        if not wait_for(backend_ready, TIMEOUT_SECONDS, "readiness backend :5000"):
            print(f"[FAIL] Log del backend: {backend_log}")
            return 1

        frontend_log_handle = open(frontend_log, "w")
        frontend_proc = subprocess.Popen(
            [npm_command(), "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            cwd=str(FRONTEND_DIR),
            stdout=frontend_log_handle,
            stderr=frontend_log_handle,
            start_new_session=os.name != "nt",
        )
        frontend_log_handle.close()
        print(f"[OK] Vite iniciado (pid {frontend_proc.pid})")

        if not wait_for(frontend_ready, TIMEOUT_SECONDS, "readiness Vite :5173"):
            print(f"[FAIL] Log de Vite: {frontend_log}")
            return 1

        print(f"[RUN] smoke HTTP contra {BASE_URL}")
        result = subprocess.run(
            [sys.executable, str(SMOKE_SCRIPT), "--base", BASE_URL],
            cwd=str(PROJECT_ROOT),
        )
        print(f"[OK] smoke finalizado con exit code {result.returncode}")

        if args.keep:
            PIDS_FILE.write_text(
                "\n".join(str(p.pid) for p in (frontend_proc, backend_proc) if p is not None),
                encoding="utf-8",
            )
            print(f"[KEEP] Servicios vivos. PIDs en {PIDS_FILE}")
        return result.returncode
    finally:
        if not args.keep:
            for proc in (frontend_proc, backend_proc):
                if proc is not None:
                    kill_process_tree(proc.pid)


if __name__ == "__main__":
    sys.exit(main())