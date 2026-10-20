from __future__ import annotations

import threading
import uuid
from pathlib import Path

from flask import current_app

from models.base import db
from models.knowledge_source import (
    KnowledgeSource,
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from services.errors import NotFoundError, ValidationError

KNOWLEDGE_ALLOWED_EXTENSIONS = {".md", ".txt"}
KNOWLEDGE_ALLOWED_ROLES = {"student", "teacher", "admin"}
KNOWLEDGE_CHUNK_SIZE = 500
KNOWLEDGE_CHUNK_OVERLAP = 50
KNOWLEDGE_CHUNK_SEPARATORS = ["\n## ", "\n### ", "\n", ". ", " "]
KNOWLEDGE_RETRIEVAL_K = 4
KNOWLEDGE_RETRIEVAL_MAX_CHARS = 1200
APPROVED_ANSWER_TYPE = KnowledgeSourceType.APPROVED_ANSWER.value

_EMBEDDINGS_LOCK = threading.Lock()
_COLLECTION_LOCK = threading.Lock()
_EMBEDDINGS = None
_COLLECTION = None


class KnowledgeServiceError(Exception):
    pass


def _get_config(name, default):
    return current_app.config.get(name, default)


def _get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        with _EMBEDDINGS_LOCK:
            if _EMBEDDINGS is None:
                from langchain_ollama import OllamaEmbeddings

                _EMBEDDINGS = OllamaEmbeddings(
                    model=_get_config("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
                    base_url=_get_config("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                )
    return _EMBEDDINGS


def _get_collection():
    global _COLLECTION
    if _COLLECTION is None:
        with _COLLECTION_LOCK:
            if _COLLECTION is None:
                import chromadb

                client = chromadb.PersistentClient(
                    path=str(_get_config("CHROMA_PERSIST_DIR", "instance/chroma"))
                )
                _COLLECTION = client.get_or_create_collection(
                    name=_get_config("CHROMA_COLLECTION", "campus_knowledge"),
                    metadata={"hnsw:space": "l2"},
                )
    return _COLLECTION


def _reset_seams():
    """Test helper: drop cached embeddings/collection so monkeypatched seams take effect."""
    global _EMBEDDINGS, _COLLECTION
    _EMBEDDINGS = None
    _COLLECTION = None


def _validate_source_type(value):
    if not isinstance(value, str):
        raise ValidationError("El tipo de fuente es obligatorio")
    allowed = {member.value for member in KnowledgeSourceType}
    if value not in allowed:
        raise ValidationError("El tipo de fuente no es válido")
    return KnowledgeSourceType(value)


def _validate_name(value):
    if not isinstance(value, str):
        raise ValidationError("El nombre de la fuente es obligatorio")
    name = value.strip()
    if not name:
        raise ValidationError("El nombre de la fuente es obligatorio")
    if len(name) > 200:
        raise ValidationError("El nombre de la fuente no puede superar los 200 caracteres")
    return name


def _validate_target_roles(values):
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    roles = []
    for role in values:
        if not isinstance(role, str) or role not in KNOWLEDGE_ALLOWED_ROLES:
            raise ValidationError("Los roles destino no son válidos")
        if role not in roles:
            roles.append(role)
    return roles


def _validate_file(file_storage):
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise ValidationError("Seleccioná un archivo para cargar")
    filename = file_storage.filename
    extension = Path(filename).suffix.lower()
    if extension not in KNOWLEDGE_ALLOWED_EXTENSIONS:
        raise ValidationError("El formato del archivo no está admitido (se aceptan .md y .txt)")
    max_bytes = int(_get_config("KNOWLEDGE_MAX_FILE_BYTES", 1048576))
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > max_bytes:
        raise ValidationError("El archivo supera el tamaño máximo permitido (1 MB)")
    if size == 0:
        raise ValidationError("El archivo está vacío o no puede procesarse")
    return extension, size


def _split_document(text):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=KNOWLEDGE_CHUNK_SIZE,
        chunk_overlap=KNOWLEDGE_CHUNK_OVERLAP,
        separators=KNOWLEDGE_CHUNK_SEPARATORS,
    )
    return [chunk for chunk in splitter.split_text(text) if chunk.strip()]


def _split_approved_answer(text):
    return [block.strip() for block in text.split("\n\n") if block.strip()]


def _chunk_text(text, source_type):
    if source_type == KnowledgeSourceType.APPROVED_ANSWER:
        return _split_approved_answer(text)
    return _split_document(text)


def _role_metadata(target_roles):
    if not target_roles:
        return {"role_student": True, "role_teacher": True, "role_admin": True}
    return {f"role_{role}": role in target_roles for role in KNOWLEDGE_ALLOWED_ROLES}


def _index_chunks(collection, embeddings, chunks, metadata):
    documents = list(chunks)
    vectors = embeddings.embed_documents(documents)
    ids = [f"{metadata['source_id']}:{index}" for index in range(len(documents))]
    metadatas = [dict(metadata) for _ in documents]
    collection.add(ids=ids, embeddings=vectors, metadatas=metadatas, documents=documents)


def serialize_source(source):
    return {
        "id": source.id,
        "name": source.name,
        "description": source.description,
        "source_type": source.source_type.value
        if hasattr(source.source_type, "value")
        else source.source_type,
        "status": source.status.value if hasattr(source.status, "value") else source.status,
        "target_roles": list(source.target_roles or []),
        "original_filename": source.original_filename,
        "file_size_bytes": source.file_size_bytes,
        "chunk_count": source.chunk_count,
        "error_message": source.error_message,
        "created_at": source.created_at.isoformat() if source.created_at else None,
        "updated_at": source.updated_at.isoformat() if source.updated_at else None,
    }


def create_source(file_storage, form_data, current_user=None):
    form_data = form_data or {}
    extension, size = _validate_file(file_storage)
    name = _validate_name(form_data.get("name"))
    source_type = _validate_source_type(form_data.get("source_type"))
    target_roles = _validate_target_roles(form_data.get("target_roles"))
    description = form_data.get("description")
    if description is None:
        description = ""
    if not isinstance(description, str):
        raise ValidationError("La descripción de la fuente no es válida")

    stored_filename = uuid.uuid4().hex + extension
    upload_dir = Path(_get_config("KNOWLEDGE_UPLOAD_DIR", "instance/knowledge"))
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_storage.stream.seek(0)
    file_bytes = file_storage.stream.read()

    source = KnowledgeSource(
        name=name,
        description=description.strip(),
        source_type=source_type,
        status=KnowledgeSourceStatus.PROCESSING,
        target_roles=target_roles,
        original_filename=file_storage.filename,
        stored_filename=stored_filename,
        file_size_bytes=size,
        chunk_count=0,
    )
    db.session.add(source)
    db.session.commit()
    db.session.refresh(source)

    stored_path = upload_dir / stored_filename
    stored_path.write_bytes(file_bytes)

    try:
        text = stored_path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            raise ValueError("El archivo no contiene texto procesable")
        chunks = _chunk_text(text, source_type)
        if not chunks:
            raise ValueError("El archivo no contiene texto procesable")
        metadata = {
            "source_id": source.id,
            "source_type": source_type.value,
            **_role_metadata(target_roles),
        }
        _index_chunks(_get_collection(), _get_embeddings(), chunks, metadata)
    except Exception as error:
        _compensate_index(source.id)
        source.status = KnowledgeSourceStatus.ERROR
        source.error_message = str(error)[:2000]
        db.session.commit()
        raise KnowledgeServiceError(
            "No se pudo procesar la fuente. Verificá que el servicio de Ollama esté "
            "disponible y que el modelo de embeddings "
            f"('{_get_config('OLLAMA_EMBED_MODEL', 'nomic-embed-text')}') esté instalado."
        ) from error

    source.status = KnowledgeSourceStatus.ACTIVE
    source.error_message = None
    source.chunk_count = len(chunks)
    db.session.commit()
    db.session.refresh(source)
    return source


def _compensate_index(source_id):
    try:
        _get_collection().delete(where={"source_id": source_id})
    except Exception:  # noqa: BLE001  (best-effort index cleanup)
        current_app.logger.warning("No se pudo compensar el índice para la fuente %s", source_id)


def list_sources():
    return list(
        db.session.execute(db.select(KnowledgeSource).order_by(KnowledgeSource.id.desc()))
        .scalars()
        .all()
    )


def get_source(source_id):
    source = db.session.get(KnowledgeSource, source_id)
    if source is None:
        raise NotFoundError("Fuente no encontrada")
    return source


def _role_value(user_role):
    if user_role is None:
        raise ValidationError("El rol del usuario no es válido")
    value = user_role.value if hasattr(user_role, "value") else user_role
    if value not in KNOWLEDGE_ALLOWED_ROLES:
        raise ValidationError("El rol del usuario no es válido")
    return value


def retrieve_for_user(query, user_role, k=KNOWLEDGE_RETRIEVAL_K):
    """Retrieve active knowledge fragments authorized for the session user role.

    Identity and role always come from the Flask session (never from the model).
    Priority is a stable sort so approved answers lead without losing similarity order.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValidationError("La consulta no puede estar vacía")
    role = _role_value(user_role)

    active_ids = list(
        db.session.execute(
            db.select(KnowledgeSource.id).where(
                KnowledgeSource.status == KnowledgeSourceStatus.ACTIVE
            )
        ).scalars()
    )
    if not active_ids:
        return []

    embedding = _get_embeddings().embed_query(query.strip())
    where = {"$and": [{"source_id": {"$in": active_ids}}, {f"role_{role}": True}]}
    raw = _get_collection().query(query_embeddings=[embedding], n_results=k, where=where)

    documents = raw.get("documents", [[]])[0] if raw.get("documents") else []
    metadatas = raw.get("metadatas", [[]])[0] if raw.get("metadatas") else []

    ranked = [
        (metadata.get("source_type"), index, document, metadata)
        for index, (document, metadata) in enumerate(zip(documents, metadatas, strict=False))
    ]
    # Stable priority sort: approved answers first, similarity order preserved within each group.
    ranked.sort(key=lambda item: item[0] != APPROVED_ANSWER_TYPE)

    source_ids = list(dict.fromkeys(item[3].get("source_id") for item in ranked))
    rows = (
        db.session.execute(
            db.select(
                KnowledgeSource.id,
                KnowledgeSource.name,
                KnowledgeSource.source_type,
            ).where(KnowledgeSource.id.in_(source_ids))
        ).all()
        if source_ids
        else []
    )
    names = {row.id: row.name for row in rows}

    results = []
    for source_type, _, document, metadata in ranked:
        source_id = metadata.get("source_id")
        text = document or ""
        results.append(
            {
                "source_name": names.get(source_id),
                "source_type": metadata.get("source_type") or source_type,
                "text": text[:KNOWLEDGE_RETRIEVAL_MAX_CHARS],
            }
        )
    return results


def delete_source(source_id):
    source = get_source(source_id)
    try:
        _get_collection().delete(where={"source_id": source_id})
    except Exception as error:
        raise KnowledgeServiceError("No se pudo eliminar la fuente. Intentá nuevamente.") from error

    upload_dir = Path(_get_config("KNOWLEDGE_UPLOAD_DIR", "instance/knowledge"))
    stored_path = upload_dir / source.stored_filename
    try:
        stored_path.unlink()
    except OSError:
        current_app.logger.warning("No se pudo borrar el archivo %s", stored_path)

    db.session.delete(source)
    db.session.commit()
