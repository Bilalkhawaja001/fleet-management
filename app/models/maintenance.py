import enum
from datetime import datetime, date

from ..extensions import db


class WorkOrderStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class WorkOrderType(str, enum.Enum):
    PREVENTIVE = "preventive"
    BREAKDOWN = "breakdown"
    ACCIDENT = "accident"


class WorkSource(str, enum.Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class PreventiveSchedule(db.Model):
    __tablename__ = "preventive_schedules"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)

    title = db.Column(db.String(120), nullable=False)
    interval_km = db.Column(db.Integer, nullable=True)
    interval_days = db.Column(db.Integer, nullable=True)

    last_done_date = db.Column(db.Date, nullable=True)
    last_done_odometer_km = db.Column(db.Integer, nullable=True)

    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("preventive_schedules", lazy=True))


class WorkOrder(db.Model):
    __tablename__ = "work_orders"

    id = db.Column(db.Integer, primary_key=True)
    wo_no = db.Column(db.String(80), nullable=True, unique=True, index=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)

    wo_type = db.Column(db.Enum(WorkOrderType), nullable=False, default=WorkOrderType.PREVENTIVE, index=True)
    work_source = db.Column(db.Enum(WorkSource), nullable=False, default=WorkSource.INTERNAL, index=True)

    status = db.Column(db.Enum(WorkOrderStatus), nullable=False, default=WorkOrderStatus.OPEN, index=True)

    opened_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    vehicle_in_workshop_at = db.Column(db.DateTime, nullable=True)
    vehicle_out_workshop_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    odometer_in = db.Column(db.Integer, nullable=True)
    odometer_out = db.Column(db.Integer, nullable=True)

    vendor_name = db.Column(db.String(160), nullable=True)

    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("work_orders", lazy=True))

    @property
    def downtime_minutes(self) -> int | None:
        if not self.vehicle_in_workshop_at or not self.vehicle_out_workshop_at:
            return None
        delta = self.vehicle_out_workshop_at - self.vehicle_in_workshop_at
        return int(delta.total_seconds() // 60)


class Part(db.Model):
    __tablename__ = "parts"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True)

    name = db.Column(db.String(160), nullable=False)
    qty = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    work_order = db.relationship("WorkOrder", backref=db.backref("parts", lazy=True, cascade="all, delete-orphan"))
