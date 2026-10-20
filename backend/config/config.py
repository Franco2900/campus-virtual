import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _resolve_backend_dir(raw_path):
    path = Path(raw_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return str(path)


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
    OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    CHROMA_PERSIST_DIR = _resolve_backend_dir(
        os.environ.get("CHROMA_PERSIST_DIR", "instance/chroma")
    )
    CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "campus_knowledge")
    KNOWLEDGE_MAX_FILE_BYTES = int(os.environ.get("KNOWLEDGE_MAX_FILE_BYTES", "1048576"))
    KNOWLEDGE_UPLOAD_DIR = _resolve_backend_dir(
        os.environ.get("KNOWLEDGE_UPLOAD_DIR", "instance/knowledge")
    )
    CHAT_HISTORY_WINDOW = int(os.environ.get("CHAT_HISTORY_WINDOW", "10"))
    CHAT_MESSAGE_MAX_LENGTH = int(os.environ.get("CHAT_MESSAGE_MAX_LENGTH", "4000"))
