from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from datetime import datetime

from decimal import Decimal

from ...models import FuelEntry, FuelEntryStatus, FuelType, Trip, UsageType, Vehicle, Driver, Role, User
from ...rbac import role_required
from .forms import FuelEntryForm

bp = Blueprint("fuel", __name__, url_prefix="/fuel")


def _choices(form: FuelEntryForm):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]
    form.driver_id.choices = [(0, "--")]
    form.driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]

    form.trip_id.choices = [(0, "--")]
    form.trip_id.choices += [(t.id, f"#{t.id} {t.origin or ''}→{t.destination_city or ''} {t.destination or ''}") for t in Trip.query.order_by(Trip.id.desc()).limit(200).all()]


@bp.get("/")
@login_required
def fuel_list():
    entries = FuelEntry.query.order_by(FuelEntry.id.desc()).all()
    return render_template("fuel/fuel_list.html", entries=entries)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def fuel_create():
    form = FuelEntryForm(fuel_type=FuelType.OFFICIAL.value)
    _choices(form)

    if form.validate_on_submit():
        trip_id = (form.trip_id.data or 0) or None
        share_pct = None
        company_amount = None
        if trip_id:
            trip = db.session.get(Trip, trip_id)
            if trip and trip.usage_type:
                if trip.usage_type in {UsageType.OFFICIAL, UsageType.MEDICAL_EMERGENCY}:
                    share_pct = 100
                elif trip.usage_type in {UsageType.SCHOOL, UsageType.EDUCATIONAL}:
                    share_pct = 50
                elif trip.usage_type == UsageType.PERSONAL:
                    share_pct = 0

        # If linked to a trip (trip closure fuel), enforce liters+amount
        if trip_id and form.amount.data is None:
            flash("Amount is required when fuel entry is linked to a trip", "danger")
            return render_template("fuel/fuel_form.html", form=form, title="New Fuel Entry")

        # If amount is present but rate missing, compute for convenience
        if form.amount.data is not None and (form.rate.data is None) and form.liters.data:
            try:
                form.rate.data = (Decimal(form.amount.data) / Decimal(form.liters.data)).quantize(Decimal("0.01"))
            except Exception:
                pass

        amt = form.amount.data
        if share_pct is not None and amt is not None:
            # amt is Decimal (WTForms DecimalField)
            company_amount = (Decimal(amt) * Decimal(share_pct) / Decimal(100)).quantize(Decimal("0.01"))

        entry = FuelEntry(
            vehicle_id=form.vehicle_id.data,
            driver_id=(form.driver_id.data or 0) or None,
            trip_id=trip_id,
            slip_no=form.slip_no.data.strip(),
            fuel_date=form.fuel_date.data,
            odometer_at_fuel=form.odometer_at_fuel.data,
            liters=form.liters.data,
            rate=form.rate.data,
            amount=form.amount.data,
            company_share_pct=share_pct,
            company_amount=company_amount,
            fuel_type=FuelType(form.fuel_type.data),
            status=FuelEntryStatus.PENDING,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Fuel entry added", "success")
        return redirect(url_for("fuel.fuel_list"))

    return render_template("fuel/fuel_form.html", form=form, title="New Fuel Entry")
