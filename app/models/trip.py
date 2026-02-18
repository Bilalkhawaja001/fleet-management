import enum
from datetime import datetime

from ..extensions import db


class TripStatus(str, enum.Enum):
    PLANNED = "planned"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"


class UsageType(str, enum.Enum):
    OFFICIAL = "official"
    PERSONAL = "personal"
    SCHOOL_VAN = "school_van"
    EDUCATION = "education"


class ItemsOwner(str, enum.Enum):
    PERSONAL = "personal"
    COMPANY = "company"


class ItemsReturnStatus(str, enum.Enum):
    RETURNED = "returned"
    NOT_RETURNED = "not_returned"
    PARTIAL = "partial"


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True, index=True)

    odometer_start = db.Column(db.Integer, nullable=True)
    odometer_end = db.Column(db.Integer, nullable=True)
    time_out = db.Column(db.DateTime, nullable=True)
    time_in = db.Column(db.DateTime, nullable=True)

    # Explicit fields used by End Trip workflow
    end_odometer = db.Column(db.Integer, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    running_km = db.Column(db.Integer, nullable=True)

    # End-trip confirmation for returnable carried items
    returnable_items_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    returnable_items_confirmed_at = db.Column(db.DateTime, nullable=True)

    # Keep as String for backward/forward compatibility with legacy values
    usage_type = db.Column(db.String(32), nullable=False, default=UsageType.OFFICIAL.value)
    department = db.Column(db.String(120), nullable=True)
    employee_name = db.Column(db.String(120), nullable=True)

    origin = db.Column(db.String(120), nullable=True)
    destination_city = db.Column(db.String(120), nullable=True)
    destination = db.Column(db.String(120), nullable=True)

    carrying_items = db.Column(db.Boolean, nullable=False, default=False)
    items_owner = db.Column(db.Enum(ItemsOwner), nullable=True)
    gatepass_no = db.Column(db.String(80), nullable=True)
    items_reason = db.Column(db.String(255), nullable=True)
    items_details = db.Column(db.Text, nullable=True)

    items_return_status = db.Column(db.Enum(ItemsReturnStatus), nullable=True)
    items_not_returned_reason = db.Column(db.Text, nullable=True)
    items_expected_return_date = db.Column(db.Date, nullable=True)

    status = db.Column(db.Enum(TripStatus), nullable=False, default=TripStatus.PLANNED)
    start_at = db.Column(db.DateTime, nullable=True)
    end_at = db.Column(db.DateTime, nullable=True)

    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index("ix_trips_status_created", "status", "created_at"),
    )

    vehicle = db.relationship("Vehicle", backref=db.backref("trips", lazy=True))
    driver = db.relationship("Driver", backref=db.backref("trips", lazy=True))

    @property
    def distance_km(self):
        if self.running_km is not None:
            return self.running_km

        start = self.odometer_start
        end = self.end_odometer if self.end_odometer is not None else self.odometer_end
        if start is None or end is None:
            return None
        return max(0, int(end) - int(start))

    @property
    def toll_amount(self):
        if not getattr(self, "expenses", None):
            return 0
        return sum([float(e.amount) for e in self.expenses if getattr(e.expense_type, "value", e.expense_type) == "toll"])

    @property
    def other_amount(self):
        if not getattr(self, "expenses", None):
            return 0
        return sum([float(e.amount) for e in self.expenses if getattr(e.expense_type, "value", e.expense_type) == "other"])

    @property
    def fuel_liters(self):
        if not getattr(self, "fuel_entries", None):
            return 0
        return sum([float(getattr(f, "liters", 0) or 0) for f in self.fuel_entries])

    @property
    def fuel_amount(self):
        if not getattr(self, "fuel_entries", None):
            return 0
        return sum([float(getattr(f, "amount", 0) or 0) for f in self.fuel_entries])

    @property
    def total_expenses(self):
        return float(self.fuel_amount or 0) + float(self.toll_amount or 0) + float(self.other_amount or 0)

    @property
    def fuel_avg_km_per_l(self):
        d = self.distance_km
        l = self.fuel_liters
        if not d or not l:
            return None
        return float(d) / float(l)

    def __repr__(self) -> str:
        return f"<Trip {self.id} {self.status}>"
