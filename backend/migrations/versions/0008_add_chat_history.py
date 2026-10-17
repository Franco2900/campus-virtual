"""Add chat history tables

Revision ID: 0008_add_chat_history
Revises: 0007_add_grading
Create Date: 2026-10-17

"""

from alembic import op
import sqlalchemy as sa


revision = "0008_add_chat_history"
down_revision = "0007_add_grading"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conversation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversation_user_id"), "conversation", ["user_id"], unique=False)
    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_message_conversation_id"), "message", ["conversation_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_message_conversation_id"), table_name="message")
    op.drop_table("message")
    op.drop_index(op.f("ix_conversation_user_id"), table_name="conversation")
    op.drop_table("conversation")
