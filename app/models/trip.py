import enum
from datetime import datetime

from ..extensions import db


class TripStatus(str, enum.Enum):
    PLANNED = "planned"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True, index=True)

    origin = db.Column(db.String(120), nullable=True)
    destination = db.Column(db.String(120), nullable=True)

    status = db.Column(db.Enum(TripStatus), nullable=False, default=TripStatus.PLANNED)
    start_at = db.Column(db.DateTime, nullable=True)
    end_at = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("trips", lazy=True))
    driver = db.relationship("Driver", backref=db.backref("trips", lazy=True))

    def __repr__(self) -> str:
        return f"<Trip {self.id} {self.status}>"
