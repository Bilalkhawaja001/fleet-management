"""documents multi file trip link

Revision ID: b1a5f990ad11
Revises: e17b3f9ac201
Create Date: 2026-02-19 13:20:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1a5f990ad11"
down_revision = "e17b3f9ac201"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("vehicle_documents", schema=None) as batch_op:
        batch_op.add_column(sa.Column("trip_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_vehicle_documents_trip_id"), ["trip_id"], unique=False)
        batch_op.create_foreign_key("fk_vehicle_documents_trip_id_trips", "trips", ["trip_id"], ["id"])

    op.create_table(
        "document_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_document_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_document_id"], ["vehicle_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_attachments_created_at"), "document_attachments", ["created_at"], unique=False)
    op.create_index(op.f("ix_document_attachments_vehicle_document_id"), "document_attachments", ["vehicle_document_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_attachments_vehicle_document_id"), table_name="document_attachments")
    op.drop_index(op.f("ix_document_attachments_created_at"), table_name="document_attachments")
    op.drop_table("document_attachments")

    with op.batch_alter_table("vehicle_documents", schema=None) as batch_op:
        batch_op.drop_constraint("fk_vehicle_documents_trip_id_trips", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_vehicle_documents_trip_id"))
        batch_op.drop_column("trip_id")
