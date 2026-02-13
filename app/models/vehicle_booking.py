import enum
from datetime import datetime

from ..extensions import db


class BookingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class VehicleBooking(db.Model):
    __tablename__ = "vehicle_bookings"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)

    employee_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(120), nullable=True)

    start_at = db.Column(db.DateTime, nullable=False, index=True)
    end_at = db.Column(db.DateTime, nullable=True, index=True)

    purpose = db.Column(db.String(255), nullable=True)

    status = db.Column(db.Enum(BookingStatus), nullable=False, default=BookingStatus.SCHEDULED, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("bookings", lazy=True))

    def __repr__(self) -> str:
        return f"<VehicleBooking {self.id} {self.vehicle_id} {self.start_at}>"
