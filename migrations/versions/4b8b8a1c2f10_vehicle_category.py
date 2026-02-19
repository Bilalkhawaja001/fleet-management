"""vehicle category

Revision ID: 4b8b8a1c2f10
Revises: 3d6ea57cdda2
Create Date: 2026-02-14 14:40:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4b8b8a1c2f10"
down_revision = "3d6ea57cdda2"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite: use batch_alter_table for safe ALTER
    with op.batch_alter_table("vehicles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=40), nullable=False, server_default="General"))

    # remove server default after backfill (optional but cleaner)
    with op.batch_alter_table("vehicles", schema=None) as batch_op:
        batch_op.alter_column("category", server_default=None)


def downgrade():
    with op.batch_alter_table("vehicles", schema=None) as batch_op:
        batch_op.drop_column("category")
