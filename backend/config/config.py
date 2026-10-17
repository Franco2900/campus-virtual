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
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))
    CHAT_HISTORY_WINDOW = int(os.environ.get("CHAT_HISTORY_WINDOW", "10"))
    CHAT_MESSAGE_MAX_LENGTH = int(os.environ.get("CHAT_MESSAGE_MAX_LENGTH", "4000"))
