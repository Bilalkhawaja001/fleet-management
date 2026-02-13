from datetime import datetime

from ..extensions import db


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    plate_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    make_model = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="active")

    current_driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    current_driver = db.relationship("Driver", foreign_keys=[current_driver_id], backref=db.backref("current_vehicles", lazy=True))

    def __repr__(self) -> str:
        return f"<Vehicle {self.plate_no}>"
