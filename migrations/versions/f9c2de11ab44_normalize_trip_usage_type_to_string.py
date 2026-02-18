"""normalize trip usage_type to string and clean legacy values

Revision ID: f9c2de11ab44
Revises: e17b3f9ac201
Create Date: 2026-02-18 18:55:00

"""

from alembic import op
import sqlalchemy as sa


revision = "f9c2de11ab44"
down_revision = "e17b3f9ac201"
branch_labels = None
depends_on = None


def upgrade():
    # Normalize legacy/bad values first
    op.execute("UPDATE trips SET usage_type='school_van' WHERE lower(usage_type) IN ('school', 'school_van')")
    op.execute("UPDATE trips SET usage_type='education' WHERE lower(usage_type) IN ('education', 'educational')")
    op.execute("UPDATE trips SET usage_type='official' WHERE lower(usage_type) IN ('medical_emergency')")

    # Normalize enum-name values to lowercase values
    op.execute("UPDATE trips SET usage_type='official' WHERE usage_type='OFFICIAL'")
    op.execute("UPDATE trips SET usage_type='personal' WHERE usage_type='PERSONAL'")
    op.execute("UPDATE trips SET usage_type='school_van' WHERE usage_type='SCHOOL_VAN'")
    op.execute("UPDATE trips SET usage_type='education' WHERE usage_type='EDUCATION'")

    # Convert column to string for stability with mixed historical data
    with op.batch_alter_table("trips", schema=None) as batch_op:
        batch_op.alter_column(
            "usage_type",
            existing_type=sa.String(length=32),
            type_=sa.String(length=32),
            existing_nullable=False,
            server_default="official",
        )


def downgrade():
    # Keep as string in downgrade path to avoid data loss/enum coercion failures
    pass
