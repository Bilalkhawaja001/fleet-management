"""add perf/security indexes

Revision ID: a91c2e7d4f11
Revises: 4b8b8a1c2f10
Create Date: 2026-02-18 13:50:00

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "a91c2e7d4f11"
down_revision = "4b8b8a1c2f10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_trips_created_at", "trips", ["created_at"], unique=False)
    op.create_index("ix_trips_status_created", "trips", ["status", "created_at"], unique=False)

    op.create_index("ix_work_orders_opened_at", "work_orders", ["opened_at"], unique=False)
    op.create_index("ix_work_orders_status_vehicle", "work_orders", ["status", "vehicle_id"], unique=False)

    op.create_index("ix_fuel_entries_created_at", "fuel_entries", ["created_at"], unique=False)
    op.create_index("ix_fuel_entries_status_date", "fuel_entries", ["status", "fuel_date"], unique=False)

    op.create_index("ix_vehicle_documents_expiry_status", "vehicle_documents", ["expiry_date", "status"], unique=False)


def downgrade():
    op.drop_index("ix_vehicle_documents_expiry_status", table_name="vehicle_documents")

    op.drop_index("ix_fuel_entries_status_date", table_name="fuel_entries")
    op.drop_index("ix_fuel_entries_created_at", table_name="fuel_entries")

    op.drop_index("ix_work_orders_status_vehicle", table_name="work_orders")
    op.drop_index("ix_work_orders_opened_at", table_name="work_orders")

    op.drop_index("ix_trips_status_created", table_name="trips")
    op.drop_index("ix_trips_created_at", table_name="trips")
