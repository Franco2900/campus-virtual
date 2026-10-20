"""Add knowledge source table

Revision ID: 0009_add_knowledge_source
Revises: 0008_add_chat_history
Create Date: 2026-10-19

"""

from alembic import op
import sqlalchemy as sa


revision = "0009_add_knowledge_source"
down_revision = "0008_add_chat_history"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_source",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "source_type",
            sa.Enum("document", "approved_answer", name="knowledgesourcetype"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("processing", "active", "error", name="knowledgesourcestatus"),
            nullable=False,
            server_default="processing",
        ),
        sa.Column("target_roles", sa.JSON(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("knowledge_source")
