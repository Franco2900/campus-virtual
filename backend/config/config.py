import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _database_uri():
    raw_path = os.environ.get("CAMPUS_DB_PATH", "instance/campus.db")
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = BACKEND_DIR / db_path
    return "sqlite:///" + db_path.as_posix()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
