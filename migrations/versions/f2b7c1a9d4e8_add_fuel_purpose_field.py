"""add fuel_purpose field

Revision ID: f2b7c1a9d4e8
Revises: a91c2e7d4f11
Create Date: 2026-02-18 14:22:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2b7c1a9d4e8"
down_revision = "a91c2e7d4f11"
branch_labels = None
depends_on = None


fuel_purpose_enum = sa.Enum(
    "official",
    "personal",
    "school_van",
    "education",
    name="fuelpurpose",
)


def upgrade():
    bind = op.get_bind()
    fuel_purpose_enum.create(bind, checkfirst=True)

    with op.batch_alter_table("fuel_entries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("fuel_purpose", fuel_purpose_enum, nullable=True))

    # Backfill from old fuel_type values where present
    op.execute(
        """
        UPDATE fuel_entries
        SET fuel_purpose = CASE
            WHEN fuel_type = 'personal' THEN 'personal'
            ELSE 'official'
        END
        WHERE fuel_purpose IS NULL
        """
    )

    with op.batch_alter_table("fuel_entries", schema=None) as batch_op:
        batch_op.alter_column("fuel_purpose", nullable=False)

    op.create_index("ix_fuel_entries_purpose_date", "fuel_entries", ["fuel_purpose", "fuel_date"], unique=False)


def downgrade():
    op.drop_index("ix_fuel_entries_purpose_date", table_name="fuel_entries")

    with op.batch_alter_table("fuel_entries", schema=None) as batch_op:
        batch_op.drop_column("fuel_purpose")

    bind = op.get_bind()
    fuel_purpose_enum.drop(bind, checkfirst=True)
