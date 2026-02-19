"""document attachment metadata fields

Revision ID: d2c7a9ef1034
Revises: b1a5f990ad11
Create Date: 2026-02-19 14:16:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d2c7a9ef1034"
down_revision = "b1a5f990ad11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("document_attachments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_document_attachments_uploaded_by_user_id"), ["uploaded_by_user_id"], unique=False)
        batch_op.create_foreign_key("fk_document_attachments_uploaded_by_user_id_users", "users", ["uploaded_by_user_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("document_attachments", schema=None) as batch_op:
        batch_op.drop_constraint("fk_document_attachments_uploaded_by_user_id_users", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_document_attachments_uploaded_by_user_id"))
        batch_op.drop_column("uploaded_by_user_id")
        batch_op.drop_column("notes")
        batch_op.drop_column("display_name")
