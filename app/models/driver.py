from datetime import datetime

from ..extensions import db


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=True)
    license_no = db.Column(db.String(80), nullable=True)
    license_expiry = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="active")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Driver {self.name}>"
