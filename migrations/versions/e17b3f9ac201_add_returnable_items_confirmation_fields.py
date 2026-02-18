"""add returnable items confirmation fields to trips

Revision ID: e17b3f9ac201
Revises: d4aa91be3321
Create Date: 2026-02-18 15:28:00

"""

from alembic import op
import sqlalchemy as sa


revision = "e17b3f9ac201"
down_revision = "d4aa91be3321"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("trips", schema=None) as batch_op:
        batch_op.add_column(sa.Column("returnable_items_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("returnable_items_confirmed_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("trips", schema=None) as batch_op:
        batch_op.drop_column("returnable_items_confirmed_at")
        batch_op.drop_column("returnable_items_confirmed")
