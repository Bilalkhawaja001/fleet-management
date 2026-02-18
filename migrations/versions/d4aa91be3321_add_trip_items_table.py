"""add trip items table

Revision ID: d4aa91be3321
Revises: c3d9f7e2b1aa
Create Date: 2026-02-18 15:12:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4aa91be3321"
down_revision = "c3d9f7e2b1aa"
branch_labels = None
depends_on = None


item_ownership = sa.Enum("personal", "company", name="itemownership")
item_uom = sa.Enum("pcs", "kg", "meter", "roll", "box", "set", "litre", "bag", "bundle", "carton", "other", name="itemuom")
item_return = sa.Enum("returnable", "not_returnable", "partial_return", "sample", name="itemreturntype")


def upgrade():
    bind = op.get_bind()
    item_ownership.create(bind, checkfirst=True)
    item_uom.create(bind, checkfirst=True)
    item_return.create(bind, checkfirst=True)

    op.create_table(
        "trip_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("ownership", item_ownership, nullable=False),
        sa.Column("gatepass_no", sa.String(length=80), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("item_description", sa.String(length=255), nullable=False),
        sa.Column("qty", sa.Numeric(12, 2), nullable=False),
        sa.Column("uom", item_uom, nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("return_type", item_return, nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trip_items_trip_id"), "trip_items", ["trip_id"], unique=False)
    op.create_index(op.f("ix_trip_items_ownership"), "trip_items", ["ownership"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_trip_items_ownership"), table_name="trip_items")
    op.drop_index(op.f("ix_trip_items_trip_id"), table_name="trip_items")
    op.drop_table("trip_items")

    bind = op.get_bind()
    item_return.drop(bind, checkfirst=True)
    item_uom.drop(bind, checkfirst=True)
    item_ownership.drop(bind, checkfirst=True)
