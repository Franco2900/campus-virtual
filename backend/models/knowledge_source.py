import enum
from datetime import UTC, datetime

from models.base import db


class KnowledgeSourceType(enum.Enum):
    DOCUMENT = "document"
    APPROVED_ANSWER = "approved_answer"


class KnowledgeSourceStatus(enum.Enum):
    PROCESSING = "processing"
    ACTIVE = "active"
    ERROR = "error"


class KnowledgeSource(db.Model):
    __tablename__ = "knowledge_source"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    source_type = db.Column(
        db.Enum(KnowledgeSourceType, values_callable=lambda enum_cls: [m.value for m in enum_cls]),
        nullable=False,
    )
    status = db.Column(
        db.Enum(
            KnowledgeSourceStatus, values_callable=lambda enum_cls: [m.value for m in enum_cls]
        ),
        nullable=False,
        default=KnowledgeSourceStatus.PROCESSING,
    )
    # List of "student"|"teacher"|"admin"; empty means it applies to every authenticated role.
    target_roles = db.Column(db.JSON, nullable=False, default=list)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False, default=0)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
