"""Portable end-to-end verifier for a Campus Virtual use case.

Starts backend and Vite, waits for readiness, runs the HTTP smoke test of the
selected use case against the Vite proxy, and guarantees cleanup of every
process tree it starts. Aborts with a clear message if the ports are already
taken, so orphan services never accumulate.

`--serve` is the entry point for interactive UI evidence: it starts the same
services fully detached from the caller process tree, records their PIDs in
`.verify-pids`, and returns immediately. A long-lived child that stays attached
keeps the caller's pipes/tree open, so an agent shell appears hung and the child
dies when that call is interrupted; breaking away avoids both problems.

Usage:
    python scripts/verify.py                          # alias of --cu cu02
    python scripts/verify.py --cu cu03                # requires scripts/smoke_cu03.py
    python scripts/verify.py --serve                  # detached services, return now (temp DB)
    python scripts/verify.py --serve --db PATH        # ... against an existing SQLite file
    python scripts/verify.py --serve --db PATH --seed-demo   # + demo data
    python scripts/verify.py --keep                   # leave services running (.verify-pids)
    python scripts/verify.py --cleanup                # stop services recorded by --keep/--serve
    python scripts/verify.py --diagnose               # read-only: ports + recorded pids

Exit code is 0 when every step PASSes, 1 when a step FAILs, 2 on abort.
"""

import argparse
import os
import re
import shutil
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
SEED_SCRIPT = PROJECT_ROOT / "scripts" / "seed_admin.py"
DEMO_SEED_SCRIPT = PROJECT_ROOT / "scripts" / "seed_demo.py"
BASE_URL = "http://127.0.0.1:5173"
BACKEND_HEALTH_URL = "http://127.0.0.1:5000/api/auth/me"
TIMEOUT_SECONDS = 60
DEFAULT_ADMIN_EMAIL = "admin@smoke.test"
DEFAULT_ADMIN_PASSWORD = "smoke-admin-123"


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


def build_run_env(db_file):
    """Run environment: explicit SQLite DB file plus admin seed credentials."""
    run_env = os.environ.copy()
    run_env["CAMPUS_DB_PATH"] = str(db_file)
    run_env.setdefault("CAMPUS_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    run_env.setdefault("CAMPUS_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    return run_env


def migrate_database(run_env):
    """Apply Alembic migrations to the isolated DB before it is used."""
    result = subprocess.run(
        [sys.executable, "-m", "flask", "--app", "app", "db", "upgrade"],
        cwd=str(BACKEND_DIR),
        env=run_env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("[FAIL] La migración de la base falló.")
        print(result.stdout)
        print(result.stderr)
        return False
    print("[OK] Migraciones aplicadas (flask db upgrade)")
    return True


def seed_database(run_env):
    """Provision the admin and demo data into the isolated DB before startup."""
    if not SEED_SCRIPT.exists():
        print(f"[SKIP] Sin script de seed ({SEED_SCRIPT.name}); se omite el aprovisionamiento.")
        return True
    result = subprocess.run(
        [sys.executable, str(SEED_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        env=run_env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("[FAIL] El seed del administrador falló.")
        print(result.stdout)
        print(result.stderr)
        return False
    print("[OK] Seed del administrador y datos de demo")
    return True


def seed_demo_data(run_env):
    """Provision demo teachers, students, enrollments, tasks and submissions."""
    if not DEMO_SEED_SCRIPT.exists():
        print(f"[SKIP] Sin script de demo ({DEMO_SEED_SCRIPT.name}); se omite.")
        return True
    result = subprocess.run(
        [sys.executable, str(DEMO_SEED_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        env=run_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("[FAIL] El seed de datos de demo fallo.")
        print(result.stdout)
        print(result.stderr)
        return False
    print("[OK] Datos de demo sembrados (profesores, estudiantes, tareas, entregas)")
    return True


def detach_creationflags():
    """Windows flags that keep a long-lived child out of the caller's tree."""
    if os.name != "nt":
        return 0
    flags = getattr(subprocess, "DETACHED_PROCESS", 0)
    flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return flags


def breakaway_creationflags():
    """Detached flags plus breakaway, so a job-owning caller releases the child."""
    return detach_creationflags() | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0)


def spawn_service(command, cwd, env, log_path):
    """Start a long-lived service detached from this process, logging to a file.

    A child that stays attached keeps the caller's pipes and process tree open:
    an agent shell then waits forever, and interrupting it kills the service.
    Detaching (with breakaway on Windows) lets the caller return immediately
    while the service keeps running until `--cleanup`.
    """
    handle = open(log_path, "w")
    try:
        if os.name == "nt":
            try:
                return subprocess.Popen(
                    command,
                    cwd=str(cwd),
                    env=env,
                    stdout=handle,
                    stderr=handle,
                    creationflags=breakaway_creationflags(),
                )
            except OSError:
                return subprocess.Popen(
                    command,
                    cwd=str(cwd),
                    env=env,
                    stdout=handle,
                    stderr=handle,
                    creationflags=detach_creationflags(),
                )
        return subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
        )
    finally:
        handle.close()

def start_services(run_env, label):
    """Start backend and Vite detached and wait for readiness.

    Returns ((backend_proc, frontend_proc), (backend_log, frontend_log)) on
    success, or (None, logs) after stopping whatever came up on failure.
    """
    backend_log = tempfile.NamedTemporaryFile(
        prefix=f"verify-{label}-backend-", suffix=".log", delete=False
    ).name
    frontend_log = tempfile.NamedTemporaryFile(
        prefix=f"verify-{label}-frontend-", suffix=".log", delete=False
    ).name

    backend_proc = spawn_service(
        [sys.executable, "run_backend.py"], BACKEND_DIR, run_env, backend_log
    )
    print(f"[OK] Backend iniciado (pid {backend_proc.pid})")
    if not wait_for(backend_ready, TIMEOUT_SECONDS, "readiness backend :5000"):
        print(f"[FAIL] Log del backend: {backend_log}")
        kill_process_tree(backend_proc.pid)
        return None, (backend_log, frontend_log)

    frontend_proc = spawn_service(
        [npm_command(), "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        FRONTEND_DIR,
        run_env,
        frontend_log,
    )
    print(f"[OK] Vite iniciado (pid {frontend_proc.pid})")
    if not wait_for(frontend_ready, TIMEOUT_SECONDS, "readiness Vite :5173"):
        print(f"[FAIL] Log de Vite: {frontend_log}")
        kill_process_tree(frontend_proc.pid)
        kill_process_tree(backend_proc.pid)
        return None, (backend_log, frontend_log)

    return (backend_proc, frontend_proc), (backend_log, frontend_log)


def serve(db_file, run_seed_admin, run_seed_demo):
    """Start detached services, record their PIDs and return immediately."""
    print("Verificando puertos libres (pre-condicion anti-duplicados)...")
    if port_is_open("127.0.0.1", 5000) or port_is_open("127.0.0.1", 5173):
        print(
            "[ABORT] Los puertos 5000/5173 estan ocupados. "
            "Ejecuta `python scripts/verify.py --diagnose` para ver quien escucha "
            "y `python scripts/verify.py --cleanup` para detener lo registrado."
        )
        return 2

    run_env = build_run_env(db_file)
    if not migrate_database(run_env):
        return 1
    if run_seed_admin and not seed_database(run_env):
        return 1
    if run_seed_demo and not seed_demo_data(run_env):
        return 1

    print(f"[SERVE] Base de datos: {db_file}")
    procs, logs = start_services(run_env, label="serve")
    if procs is None:
        return 1

    PIDS_FILE.write_text("\n".join(str(p.pid) for p in procs), encoding="utf-8")
    print(f"[SERVE] Servicios vivos y desligados. PIDs en {PIDS_FILE}")
    print(f"[SERVE] Frontend {BASE_URL} | backend http://127.0.0.1:5000")
    print(f"[SERVE] Logs: {logs[0]} | {logs[1]}")
    print("[SERVE] Detener: python scripts/verify.py --cleanup")
    return 0


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
    parser.add_argument(
        "--serve",
        action="store_true",
        help="iniciar backend y Vite desligados y volver (pids en .verify-pids)",
    )
    parser.add_argument(
        "--db",
        help="usar un archivo SQLite existente en lugar de una base temporal aislada",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="sembrar datos de demo (profesores, estudiantes, tareas, entregas)",
    )
    parser.add_argument(
        "--seed-admin",
        action="store_true",
        help="sembrar el administrador aunque se use --db (por defecto solo con base temporal)",
    )
    parser.add_argument("--cleanup", action="store_true", help="detener servicios registrados")
    parser.add_argument("--diagnose", action="store_true", help="estado de puertos y pids (read-only)")
    args = parser.parse_args()

    if args.diagnose:
        diagnose()
        return 0

    if args.cleanup:
        return 0 if stop_recorded_services() else 1

    if args.serve:
        if args.db:
            db_file = Path(args.db).resolve()
            if not db_file.exists():
                print(f"[ABORT] No existe la base indicada: {db_file}")
                return 2
            run_seed_admin = args.seed_admin
        else:
            db_dir = tempfile.mkdtemp(prefix="verify-serve-db-")
            db_file = Path(db_dir) / "campus.db"
            run_seed_admin = True
        return serve(db_file, run_seed_admin, args.seed_demo)

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

    db_dir = tempfile.mkdtemp(prefix=f"verify-{args.cu}-db-")
    run_env = build_run_env(Path(db_dir) / "campus.db")
    if not migrate_database(run_env) or not seed_database(run_env):
        shutil.rmtree(db_dir, ignore_errors=True)
        return 1

    procs, _logs = start_services(run_env, label=args.cu)
    try:
        if procs is None:
            return 1

        print(f"[RUN] smoke {args.cu} contra {BASE_URL}")
        result = subprocess.run(
            [sys.executable, str(smoke_path), "--base", BASE_URL],
            cwd=str(PROJECT_ROOT),
            env=run_env,
        )
        print(f"[OK] smoke finalizado con exit code {result.returncode}")

        if args.keep:
            PIDS_FILE.write_text("\n".join(str(p.pid) for p in procs), encoding="utf-8")
            print(f"[KEEP] Servicios vivos. PIDs en {PIDS_FILE}")
        return result.returncode
    finally:
        if not args.keep:
            for proc in procs or ():
                kill_process_tree(proc.pid)
            shutil.rmtree(db_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())