import enum
from datetime import datetime, date

from ..extensions import db


class ScheduleMode(str, enum.Enum):
    KM = "km"
    TIME = "time"
    BOTH = "both"


class MaintenancePlan(db.Model):
    __tablename__ = "maintenance_plans"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True, index=True)

    name = db.Column(db.String(160), nullable=False)
    schedule_mode = db.Column(db.Enum(ScheduleMode), nullable=False, default=ScheduleMode.TIME)

    interval_km = db.Column(db.Integer, nullable=True)
    interval_days = db.Column(db.Integer, nullable=True)

    last_service_meter = db.Column(db.Integer, nullable=True)
    last_service_date = db.Column(db.Date, nullable=True)

    next_due_meter = db.Column(db.Integer, nullable=True)
    next_due_date = db.Column(db.Date, nullable=True, index=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("maintenance_plans", lazy=True))
