import enum
from datetime import datetime, date

from ..extensions import db


class NotificationType(str, enum.Enum):
    DOC_EXPIRY = "doc_expiry"
    DOC_MISSING = "doc_missing"
    PM_DUE = "pm_due"
    WO_OVERDUE = "wo_overdue"
    FUEL_PENDING = "fuel_pending"
    INCIDENT_PENDING = "incident_pending"


class NotificationSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(db.Enum(NotificationType), nullable=False, index=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True, index=True)
    doc_id = db.Column(db.Integer, db.ForeignKey("vehicle_documents.id"), nullable=True, index=True)
    wo_id = db.Column(db.Integer, db.ForeignKey("work_orders.id"), nullable=True, index=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=True, index=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=True, index=True)

    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    severity = db.Column(db.Enum(NotificationSeverity), nullable=False, default=NotificationSeverity.INFO)

    due_date = db.Column(db.Date, nullable=True, index=True)

    is_read = db.Column(db.Boolean, nullable=False, default=False)
    dismissed_until = db.Column(db.DateTime, nullable=True)
    last_shown_on = db.Column(db.Date, nullable=True)  # daily popup throttle

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("notifications", lazy=True))

    def __repr__(self) -> str:
        return f"<Notification {self.type} {self.severity} read={self.is_read}>"
