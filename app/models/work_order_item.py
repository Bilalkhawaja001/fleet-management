import enum
from datetime import datetime

from ..extensions import db


class WorkOrderType(str, enum.Enum):
    PREVENTIVE = "preventive"
    BREAKDOWN = "breakdown"
    ACCIDENT = "accident"


class WorkSource(str, enum.Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class WorkOrderStatus2(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class JobType(str, enum.Enum):
    REPAIR = "repair"
    REPLACE = "replace"
    SERVICE = "service"
    INSPECT = "inspect"


class WorkOrderItem(db.Model):
    __tablename__ = "work_order_items"

    id = db.Column(db.Integer, primary_key=True)
    wo_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=False, index=True)

    category = db.Column(db.String(80), nullable=True)
    subsystem = db.Column(db.String(80), nullable=True)
    component = db.Column(db.String(120), nullable=True)

    job_type = db.Column(db.Enum(JobType), nullable=False, default=JobType.INSPECT)
    detail_text = db.Column(db.Text, nullable=True)

    labor_cost = db.Column(db.Numeric(12, 2), nullable=True)
    parts_cost = db.Column(db.Numeric(12, 2), nullable=True)

    attachment_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
