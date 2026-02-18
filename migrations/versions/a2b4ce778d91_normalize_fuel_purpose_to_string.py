"""normalize fuel_purpose to string and clean enum values

Revision ID: a2b4ce778d91
Revises: f9c2de11ab44
Create Date: 2026-02-18 19:05:00

"""

from alembic import op
import sqlalchemy as sa


revision = "a2b4ce778d91"
down_revision = "f9c2de11ab44"
branch_labels = None
depends_on = None


def upgrade():
    # normalize uppercase enum names to lowercase values
    op.execute("UPDATE fuel_entries SET fuel_purpose='official' WHERE fuel_purpose='OFFICIAL'")
    op.execute("UPDATE fuel_entries SET fuel_purpose='personal' WHERE fuel_purpose='PERSONAL'")
    op.execute("UPDATE fuel_entries SET fuel_purpose='school_van' WHERE fuel_purpose='SCHOOL_VAN'")
    op.execute("UPDATE fuel_entries SET fuel_purpose='education' WHERE fuel_purpose='EDUCATION'")

    # Normalize possible legacy spellings
    op.execute("UPDATE fuel_entries SET fuel_purpose='school_van' WHERE lower(fuel_purpose)='school'")

    with op.batch_alter_table("fuel_entries", schema=None) as batch_op:
        batch_op.alter_column(
            "fuel_purpose",
            existing_type=sa.String(length=32),
            type_=sa.String(length=32),
            existing_nullable=False,
            server_default="official",
        )


def downgrade():
    pass
