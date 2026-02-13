import enum
from datetime import datetime

from ..extensions import db


class TripExpenseType(str, enum.Enum):
    TOLL = "toll"
    OTHER = "other"


class TripExpense(db.Model):
    __tablename__ = "trip_expenses"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)

    expense_type = db.Column(db.Enum(TripExpenseType), nullable=False, index=True)
    expense_date = db.Column(db.Date, nullable=True, index=True)

    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    attachment_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    trip = db.relationship("Trip", backref=db.backref("expenses", lazy=True, cascade="all, delete-orphan"))
