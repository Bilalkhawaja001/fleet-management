import enum
from datetime import datetime, date

from ..extensions import db


class WorkOrderStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"


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
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)

    status = db.Column(db.Enum(WorkOrderStatus), nullable=False, default=WorkOrderStatus.OPEN)
    opened_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("work_orders", lazy=True))


class Part(db.Model):
    __tablename__ = "parts"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True)

    name = db.Column(db.String(160), nullable=False)
    qty = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    work_order = db.relationship("WorkOrder", backref=db.backref("parts", lazy=True, cascade="all, delete-orphan"))
