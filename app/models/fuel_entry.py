import enum
from datetime import datetime, date

from ..extensions import db


class FuelType(str, enum.Enum):
    OFFICIAL = "official"
    PERSONAL = "personal"


class FuelEntryStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class FuelEntry(db.Model):
    __tablename__ = "fuel_entries"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True, index=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=True, index=True)

    slip_no = db.Column(db.String(80), nullable=False, unique=True, index=True)

    fuel_date = db.Column(db.Date, nullable=False, index=True)
    odometer_at_fuel = db.Column(db.Integer, nullable=True)

    liters = db.Column(db.Numeric(10, 2), nullable=False)
    rate = db.Column(db.Numeric(12, 2), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=True)

    # Company fuel share policy based on linked trip usage_type
    company_share_pct = db.Column(db.Integer, nullable=True)  # 0/50/100
    company_amount = db.Column(db.Numeric(12, 2), nullable=True)

    fuel_type = db.Column(db.Enum(FuelType), nullable=False, default=FuelType.OFFICIAL, index=True)

    status = db.Column(db.Enum(FuelEntryStatus), nullable=False, default=FuelEntryStatus.PENDING, index=True)
    verified_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)

    attachment_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("fuel_entries", lazy=True))
    driver = db.relationship("Driver", backref=db.backref("fuel_entries", lazy=True))
    trip = db.relationship("Trip", backref=db.backref("fuel_entries", lazy=True))
    verified_by = db.relationship("User", foreign_keys=[verified_by_user_id])

    def __repr__(self) -> str:
        return f"<FuelEntry {self.slip_no} {self.vehicle_id} {self.status}>"
