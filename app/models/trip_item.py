import enum
from datetime import datetime

from ..extensions import db


class ItemOwnership(str, enum.Enum):
    PERSONAL = "personal"
    COMPANY = "company"


class ItemUom(str, enum.Enum):
    PCS = "pcs"
    KG = "kg"
    METER = "meter"
    ROLL = "roll"
    BOX = "box"
    SET = "set"
    LITRE = "litre"
    BAG = "bag"
    BUNDLE = "bundle"
    CARTON = "carton"
    OTHER = "other"


class ItemReturnType(str, enum.Enum):
    RETURNABLE = "returnable"
    NOT_RETURNABLE = "not_returnable"
    PARTIAL_RETURN = "partial_return"
    SAMPLE = "sample"


class TripItem(db.Model):
    __tablename__ = "trip_items"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)

    ownership = db.Column(db.Enum(ItemOwnership), nullable=False, index=True)

    gatepass_no = db.Column(db.String(80), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    item_description = db.Column(db.String(255), nullable=False)
    qty = db.Column(db.Numeric(12, 2), nullable=False)
    uom = db.Column(db.Enum(ItemUom), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    return_type = db.Column(db.Enum(ItemReturnType), nullable=False)
    notes = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    trip = db.relationship("Trip", backref=db.backref("trip_items", lazy=True, cascade="all, delete-orphan"))
