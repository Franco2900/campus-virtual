"""Portable end-to-end verifier for a Campus Virtual use case.

Starts backend and Vite, waits for readiness, runs the HTTP smoke test of the
selected use case against the Vite proxy, and guarantees cleanup of every
process tree it starts. Aborts with a clear message if the ports are already
taken, so orphan services never accumulate.

Usage:
    python scripts/verify.py                          # alias of --cu cu02
    python scripts/verify.py --cu cu03                # requires scripts/smoke_cu03.py
    python scripts/verify.py --keep                   # leave services running (.verify-pids)
    python scripts/verify.py --cleanup                # stop services recorded by --keep
    python scripts/verify.py --diagnose               # read-only: ports + recorded pids

Exit code is 0 when every step PASSes, 1 when a step FAILs, 2 on abort.
"""

import argparse
import os
import re
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
PIDS_FILE = PROJECT_ROOT / "scripts" / ".verify-pids"
LEGACY_PIDS_FILE = PROJECT_ROOT / "scripts" / ".cu02-pids"
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


def resolve_smoke(cu):
    if not re.fullmatch(r"cu\d{2}", cu):
        return None
    path = PROJECT_ROOT / "scripts" / f"smoke_{cu}.py"
    return path if path.exists() else None


def collect_pids(paths):
    pids = []
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().isdigit():
                pids.append(int(line.strip()))
    return sorted(set(pids))


def listening_pids(port):
    command = ["netstat", "-ano"] if sys.platform == "win32" else ["ss", "-ltnp"]
    try:
        output = subprocess.run(command, capture_output=True, text=True).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    pids = []
    for line in output.splitlines():
        if f":{port}" not in line:
            continue
        if sys.platform == "win32":
            if "LISTENING" not in line:
                continue
            parts = line.split()
            if parts and parts[-1].isdigit():
                pids.append(int(parts[-1]))
        else:
            match = re.search(r"pid=(\d+)", line)
            if match:
                pids.append(int(match.group(1)))
    return sorted(set(pids))


def diagnose():
    print("== Diagnostico (solo lectura, no detiene nada) ==")
    for host, port, name in (
        ("127.0.0.1", 5000, "backend"),
        ("127.0.0.1", 5173, "frontend (Vite)"),
    ):
        if port_is_open(host, port):
            pids = listening_pids(port)
            hint = f" PID(s): {', '.join(str(p) for p in pids)}" if pids else ""
            print(f"[OCUPADO] {name} escuchando en {host}:{port}{hint}")
        else:
            print(f"[LIBRE]   {name} no escucha en {host}:{port}")
    recorded = collect_pids((PIDS_FILE, LEGACY_PIDS_FILE))
    if recorded:
        print(
            "Servicios registrados: "
            + ", ".join(str(pid) for pid in recorded)
            + " (sugerencia: `python scripts/verify.py --cleanup`)"
        )
    else:
        print("Sin servicios registrados en .verify-pids / .cu02-pids.")
    print(
        "Sugerencia si algo sigue ocupado: "
        "`python scripts/verify.py --cleanup` o cerrar el proceso que escucha el puerto."
    )


def stop_recorded_services():
    recorded = collect_pids((PIDS_FILE, LEGACY_PIDS_FILE))
    if not recorded:
        print("[CLEANUP] No hay pids registrados; nada que detener.")
        return True
    for pid in recorded:
        print(f"[CLEANUP] Terminando PID {pid}")
        kill_process_tree(pid)
    PIDS_FILE.unlink(missing_ok=True)
    LEGACY_PIDS_FILE.unlink(missing_ok=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cu", default="cu02", help="CU a verificar (debe existir scripts/smoke_<cu>.py)"
    )
    parser.add_argument("--keep", action="store_true", help="dejar backend y Vite corriendo")
    parser.add_argument("--cleanup", action="store_true", help="detener servicios registrados")
    parser.add_argument("--diagnose", action="store_true", help="estado de puertos y pids (read-only)")
    args = parser.parse_args()

    if args.diagnose:
        diagnose()
        return 0

    if args.cleanup:
        return 0 if stop_recorded_services() else 1

    smoke_path = resolve_smoke(args.cu.strip().lower())
    if smoke_path is None:
        print(
            f"[ABORT] No existe scripts/smoke_{args.cu}.py. "
            "Crea el smoke HTTP del CU primero (patron: scripts/smoke_cu02.py)."
        )
        return 2

    print("Verificando puertos libres (pre-condicion anti-duplicados)...")
    if port_is_open("127.0.0.1", 5000) or port_is_open("127.0.0.1", 5173):
        print(
            "[ABORT] Los puertos 5000/5173 estan ocupados. "
            "Ejecuta `python scripts/verify.py --diagnose` para ver quien escucha "
            "y `python scripts/verify.py --cleanup` para detener lo registrado."
        )
        return 2

    backend_log = tempfile.NamedTemporaryFile(
        prefix=f"verify-{args.cu}-backend-", suffix=".log", delete=False
    ).name
    frontend_log = tempfile.NamedTemporaryFile(
        prefix=f"verify-{args.cu}-frontend-", suffix=".log", delete=False
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

        print(f"[RUN] smoke {args.cu} contra {BASE_URL}")
        result = subprocess.run(
            [sys.executable, str(smoke_path), "--base", BASE_URL],
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