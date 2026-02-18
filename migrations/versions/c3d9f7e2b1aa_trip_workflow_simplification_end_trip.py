"""trip workflow simplification + end trip fields

Revision ID: c3d9f7e2b1aa
Revises: f2b7c1a9d4e8
Create Date: 2026-02-18 14:50:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d9f7e2b1aa"
down_revision = "f2b7c1a9d4e8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("trips", schema=None) as batch_op:
        batch_op.add_column(sa.Column("end_odometer", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("end_time", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("running_km", sa.Integer(), nullable=True))

    # Map legacy trip purpose values to new simplified set
    op.execute("UPDATE trips SET usage_type = 'official' WHERE usage_type = 'medical_emergency'")
    op.execute("UPDATE trips SET usage_type = 'school_van' WHERE usage_type = 'school'")
    op.execute("UPDATE trips SET usage_type = 'education' WHERE usage_type = 'educational'")

    # Backward-compatible data copy for existing completed trips
    op.execute("UPDATE trips SET end_time = time_in WHERE end_time IS NULL AND time_in IS NOT NULL")
    op.execute("UPDATE trips SET end_odometer = odometer_end WHERE end_odometer IS NULL AND odometer_end IS NOT NULL")
    op.execute(
        """
        UPDATE trips
        SET running_km = CASE
            WHEN odometer_start IS NOT NULL AND end_odometer IS NOT NULL AND end_odometer >= odometer_start
            THEN end_odometer - odometer_start
            ELSE running_km
        END
        WHERE running_km IS NULL
        """
    )


def downgrade():
    with op.batch_alter_table("trips", schema=None) as batch_op:
        batch_op.drop_column("running_km")
        batch_op.drop_column("end_time")
        batch_op.drop_column("end_odometer")
