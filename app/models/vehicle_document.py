import enum
from datetime import datetime, date

from ..extensions import db


class VehicleDocType(str, enum.Enum):
    INSURANCE = "insurance"
    FITNESS = "fitness"
    REGISTRATION = "registration"
    PERMIT = "permit"
    TAX = "tax"


class VehicleDocStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class VehicleDocument(db.Model):
    __tablename__ = "vehicle_documents"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)

    doc_type = db.Column(db.Enum(VehicleDocType), nullable=False, index=True)
    doc_name = db.Column(db.String(160), nullable=True)
    doc_number = db.Column(db.String(120), nullable=True)

    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=False, index=True)

    status = db.Column(db.Enum(VehicleDocStatus), nullable=False, default=VehicleDocStatus.ACTIVE, index=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_vehicle_documents_expiry_status", "expiry_date", "status"),
    )

    vehicle = db.relationship("Vehicle", backref=db.backref("documents", lazy=True))
    trip = db.relationship("Trip", backref=db.backref("documents", lazy=True))

    def __repr__(self) -> str:
        return f"<VehicleDocument {self.vehicle_id} {self.doc_type} {self.status}>"
