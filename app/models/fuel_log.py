from datetime import datetime

from ..extensions import db


class FuelLog(db.Model):
    __tablename__ = "fuel_logs"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False, index=True)
    filled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    liters = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=True)
    odometer_km = db.Column(db.Integer, nullable=True)

    vendor = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle", backref=db.backref("fuel_logs", lazy=True))
