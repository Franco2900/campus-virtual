import io

import pytest
from werkzeug.datastructures import FileStorage

from models.base import db
from models.knowledge_source import KnowledgeSource, KnowledgeSourceStatus
from models.user import UserRole
from services import knowledge_service
from services.errors import NotFoundError, ValidationError


def _file_storage(content, filename="guia.md"):
    return FileStorage(
        stream=io.BytesIO(content.encode("utf-8")),
        filename=filename,
        content_type="text/markdown",
    )


class _FakeEmbeddings:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def embed_documents(self, documents):
        self.calls.append(("embed_documents", list(documents)))
        if self.fail:
            raise RuntimeError("ollama connection refused")
        return [[float(index), 0.0] for index, _ in enumerate(documents)]

    def embed_query(self, text):
        if self.fail:
            raise RuntimeError("ollama connection refused")
        return [0.0, 1.0]


class _FakeCollection:
    def __init__(self):
        self.rows = {}
        self.delete_calls = []
        self.add_calls = []
        self.fail_delete = False

    def add(self, ids, embeddings, metadatas, documents):
        self.add_calls.append(
            {"ids": list(ids), "metadatas": list(metadatas), "documents": list(documents)}
        )
        for index, chunk_id in enumerate(ids):
            self.rows[chunk_id] = {
                "document": documents[index],
                "metadata": metadatas[index],
                "embedding": embeddings[index],
            }

    def delete(self, where):
        self.delete_calls.append(where)
        if self.fail_delete:
            raise RuntimeError("chroma unavailable")
        source_id = where.get("source_id")
        for chunk_id in [
            cid for cid, row in self.rows.items() if row["metadata"]["source_id"] == source_id
        ]:
            del self.rows[chunk_id]

    def query(self, query_embeddings, n_results, where):
        # Applies the boolean role flags + source_id filter the service relies on.
        matches = []
        for chunk_id, row in self.rows.items():
            if not _row_matches(row["metadata"], where):
                continue
            matches.append((chunk_id, row))
        matches.sort(key=lambda item: item[0])
        limited = matches[:n_results]
        return {
            "ids": [[chunk_id for chunk_id, _ in limited]],
            "documents": [[row["document"] for _, row in limited]],
            "metadatas": [[row["metadata"] for _, row in limited]],
        }


def _row_matches(metadata, where):
    if "source_id" in where and metadata["source_id"] != where["source_id"]:
        return False
    if "$and" in where:
        for clause in where["$and"]:
            if "source_id" in clause and metadata["source_id"] not in clause["source_id"]["$in"]:
                return False
            for key, value in clause.items():
                if key == "source_id":
                    continue
                if metadata.get(key) != value:
                    return False
    return True


@pytest.fixture
def seams(monkeypatch, app):
    embeddings = _FakeEmbeddings()
    collection = _FakeCollection()
    monkeypatch.setattr(knowledge_service, "_get_embeddings", lambda: embeddings)
    monkeypatch.setattr(knowledge_service, "_get_collection", lambda: collection)
    knowledge_service._reset_seams()
    return embeddings, collection


@pytest.fixture
def upload_dir(tmp_path):
    return tmp_path / "knowledge"


# Validation (A4)


@pytest.mark.parametrize(
    "filename",
    ["guia.pdf", "notas.docx", "archivo", "virus.exe"],
)
def test_invalid_extension_is_rejected_without_row(app, seams, upload_dir, filename):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        with pytest.raises(ValidationError):
            knowledge_service.create_source(
                _file_storage("contenido", filename=filename),
                {"name": "Guía", "source_type": "document", "target_roles": []},
            )
        assert db.session.execute(db.select(db.func.count(KnowledgeSource.id))).scalar_one() == 0


def test_oversized_file_is_rejected_without_row(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    app.config["KNOWLEDGE_MAX_FILE_BYTES"] = 10
    with app.app_context():
        with pytest.raises(ValidationError):
            knowledge_service.create_source(
                _file_storage("x" * 50),
                {"name": "Guía", "source_type": "document", "target_roles": []},
            )
        assert db.session.execute(db.select(db.func.count(KnowledgeSource.id))).scalar_one() == 0


@pytest.mark.parametrize(
    "form",
    [
        {"name": "", "source_type": "document"},
        {"name": "   ", "source_type": "document"},
        {"source_type": "document"},
        {"name": "Guía", "source_type": "inventado"},
        {"name": "Guía"},
        {"name": "Guía", "source_type": "document", "target_roles": ["wizard"]},
    ],
)
def test_invalid_fields_are_rejected_without_row(app, seams, upload_dir, form):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        with pytest.raises(ValidationError):
            knowledge_service.create_source(_file_storage("contenido"), form)
        assert db.session.execute(db.select(db.func.count(KnowledgeSource.id))).scalar_one() == 0


# State transitions (A1 / A5)


def test_successful_create_activates_source_with_chunk_count(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("## Sección\n\nContenido de prueba para indexar."),
            {"name": "Guía", "source_type": "document", "target_roles": ["student"]},
        )
        assert source.status == KnowledgeSourceStatus.ACTIVE
        assert source.error_message is None
        assert source.chunk_count == len(collection.rows)
        assert source.chunk_count >= 1
        assert (upload_dir / source.stored_filename).exists()
        stored = next(iter(collection.rows.values()))["metadata"]
        assert stored["source_id"] == source.id
        assert stored["source_type"] == "document"
        assert stored["role_student"] is True
        assert stored["role_teacher"] is False
        assert stored["role_admin"] is False


def test_empty_roles_are_indexed_for_every_role(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("Contenido"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        metadata = next(iter(collection.rows.values()))["metadata"]
        assert metadata["role_student"] is True
        assert metadata["role_teacher"] is True
        assert metadata["role_admin"] is True
        assert source.target_roles == []


def test_embedding_failure_marks_error_and_compensates_index(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    embeddings, collection = seams
    embeddings.fail = True
    with app.app_context():
        with pytest.raises(knowledge_service.KnowledgeServiceError):
            knowledge_service.create_source(
                _file_storage("Contenido"),
                {"name": "Guía", "source_type": "document", "target_roles": []},
            )
        rows = db.session.execute(db.select(KnowledgeSource)).scalars().all()
        assert len(rows) == 1
        assert rows[0].status == KnowledgeSourceStatus.ERROR
        assert rows[0].error_message
        assert {"source_id": rows[0].id} in collection.delete_calls
        assert collection.rows == {}


# Chunking


def test_document_source_is_chunked_by_splitter(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    body = "\n## Uno\n" + ("texto " * 200) + "\n## Dos\n" + ("mas " * 200)
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage(body),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        assert source.chunk_count > 1
        assert all(len(row["document"]) <= 500 for row in collection.rows.values())


def test_approved_answer_source_is_one_chunk_per_block(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    body = "Pregunta uno\n\nPregunta dos\n\n\n\nPregunta tres"
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage(body),
            {"name": "FAQ", "source_type": "approved_answer", "target_roles": []},
        )
        assert source.chunk_count == 3
        assert all(
            row["metadata"]["source_type"] == "approved_answer" for row in collection.rows.values()
        )


# Listing / retrieval / deletion


def test_list_sources_orders_by_id_descending(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        first = knowledge_service.create_source(
            _file_storage("uno"),
            {"name": "Uno", "source_type": "document", "target_roles": []},
        )
        second = knowledge_service.create_source(
            _file_storage("dos"),
            {"name": "Dos", "source_type": "document", "target_roles": []},
        )
        ids = [row.id for row in knowledge_service.list_sources()]
        assert ids == [second.id, first.id]


def test_get_source_missing_raises_not_found(app):
    with app.app_context(), pytest.raises(NotFoundError):
        knowledge_service.get_source(9999)


def test_serialize_target_roles_empty_means_all(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("contenido"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        payload = knowledge_service.serialize_source(source)
        assert payload["target_roles"] == []
        assert payload["status"] == "active"
        assert payload["source_type"] == "document"


def test_delete_source_removes_index_file_and_row(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("contenido"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        source_id = source.id
        stored_path = upload_dir / source.stored_filename
        assert stored_path.exists()

        knowledge_service.delete_source(source_id)

        assert collection.delete_calls == [{"source_id": source_id}]
        assert collection.rows == {}
        assert not stored_path.exists()
        assert db.session.get(KnowledgeSource, source_id) is None


def test_delete_source_missing_raises_not_found(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    with app.app_context():
        with pytest.raises(NotFoundError):
            knowledge_service.delete_source(9999)
        assert collection.delete_calls == []


def test_delete_index_failure_keeps_row_and_raises(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("contenido"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        source_id = source.id
        collection.fail_delete = True
        with pytest.raises(knowledge_service.KnowledgeServiceError):
            knowledge_service.delete_source(source_id)
        assert db.session.get(KnowledgeSource, source_id) is not None


def test_delete_is_tolerant_to_missing_file(app, seams, upload_dir, monkeypatch):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    _, collection = seams
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("contenido"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        source_id = source.id

        def _boom(self):
            raise OSError("locked")

        monkeypatch.setattr("pathlib.Path.unlink", _boom)

        knowledge_service.delete_source(source_id)

        assert db.session.get(KnowledgeSource, source_id) is None
        assert collection.delete_calls == [{"source_id": source_id}]


# Retrieval scoped by role (rules 5/7/8/13)


def _retrieve(role, query="inscripciones"):
    return knowledge_service.retrieve_for_user(query, role)


def test_retrieve_for_user_without_active_sources_returns_empty(app, seams):
    with app.app_context():
        assert _retrieve(UserRole.STUDENT) == []


def test_retrieve_for_user_excludes_sources_restricted_to_other_role(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        knowledge_service.create_source(
            _file_storage("Contenido solo para profesores sobre inscripciones"),
            {"name": "Guía docente", "source_type": "document", "target_roles": ["teacher"]},
        )
        # Rule 7: a student must not recover a source restricted to teachers.
        assert _retrieve(UserRole.STUDENT) == []
        assert _retrieve(UserRole.TEACHER)[0]["source_name"] == "Guía docente"


def test_retrieve_for_user_prioritizes_approved_answers(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        knowledge_service.create_source(
            _file_storage("Documento general sobre inscripciones"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        knowledge_service.create_source(
            _file_storage("Respuesta aprobada sobre inscripciones"),
            {"name": "FAQ", "source_type": "approved_answer", "target_roles": []},
        )
        results = _retrieve(UserRole.STUDENT)

    assert results[0]["source_type"] == "approved_answer"
    assert results[0]["source_name"] == "FAQ"
    assert {item["source_type"] for item in results} == {"approved_answer", "document"}


def test_retrieve_for_user_ignores_deleted_source(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        source = knowledge_service.create_source(
            _file_storage("Contenido sobre inscripciones"),
            {"name": "Guía", "source_type": "document", "target_roles": []},
        )
        assert _retrieve(UserRole.STUDENT)
        knowledge_service.delete_source(source.id)
        # A7: a deleted source is no longer recovered.
        assert _retrieve(UserRole.STUDENT) == []


def test_retrieve_for_user_ignores_non_active_source(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    embeddings, _ = seams
    embeddings.fail = True
    with app.app_context():
        with pytest.raises(knowledge_service.KnowledgeServiceError):
            knowledge_service.create_source(
                _file_storage("Contenido sobre inscripciones"),
                {"name": "Guía", "source_type": "document", "target_roles": []},
            )
        # A source in error state is excluded from retrieval (rules 5/13).
        assert _retrieve(UserRole.STUDENT) == []


def test_retrieve_for_user_truncates_text_to_max_chars(app, seams, upload_dir):
    app.config["KNOWLEDGE_UPLOAD_DIR"] = str(upload_dir)
    with app.app_context():
        body = "aprobada " * 400
        knowledge_service.create_source(
            _file_storage(body),
            {"name": "FAQ", "source_type": "approved_answer", "target_roles": []},
        )
        results = _retrieve(UserRole.STUDENT)

    assert results
    assert all(
        len(item["text"]) <= knowledge_service.KNOWLEDGE_RETRIEVAL_MAX_CHARS for item in results
    )


def test_retrieve_for_user_rejects_blank_query(app, seams):
    with app.app_context(), pytest.raises(ValidationError):
        knowledge_service.retrieve_for_user("   ", UserRole.STUDENT)


def test_retrieve_for_user_rejects_invalid_role(app, seams):
    with app.app_context(), pytest.raises(ValidationError):
        knowledge_service.retrieve_for_user("inscripciones", "wizard")
