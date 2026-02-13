import enum
from datetime import datetime

from ..extensions import db


class IncidentType(str, enum.Enum):
    ACCIDENT = "accident"
    DAMAGE = "damage"
    THEFT = "theft"
    OTHER = "other"


class IncidentSeverity(str, enum.Enum):
    MINOR = "minor"
    MAJOR = "major"
    TOTAL_LOSS = "total_loss"


class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    incident_no = db.Column(db.String(80), nullable=False, unique=True, index=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True, index=True)

    incident_dt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    location = db.Column(db.String(200), nullable=True)

    incident_type = db.Column(db.Enum(IncidentType), nullable=False, default=IncidentType.OTHER, index=True)
    severity = db.Column(db.Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MINOR, index=True)

    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.Enum(IncidentStatus), nullable=False, default=IncidentStatus.REPORTED, index=True)

    approver_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_note = db.Column(db.Text, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)

    claim_no = db.Column(db.String(120), nullable=True)
    claim_status = db.Column(db.Enum(ClaimStatus), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("incidents", lazy=True))
    driver = db.relationship("Driver", backref=db.backref("incidents", lazy=True))
    approver = db.relationship("User", foreign_keys=[approver_user_id])


class IncidentAttachment(db.Model):
    __tablename__ = "incident_attachments"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id"), nullable=False, index=True)

    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    incident = db.relationship("Incident", backref=db.backref("attachments", lazy=True, cascade="all, delete-orphan"))
