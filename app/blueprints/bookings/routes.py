from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import BookingStatus, Vehicle, VehicleBooking, Role
from ...rbac import role_required
from .forms import BookingForm

bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _vehicle_choices(form: BookingForm):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]


@bp.get("/")
@login_required
def booking_list():
    rows = VehicleBooking.query.order_by(VehicleBooking.start_at.desc()).limit(500).all()
    return render_template("bookings/booking_list.html", rows=rows)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def booking_create():
    form = BookingForm(start_at=datetime.now())
    _vehicle_choices(form)

    if form.validate_on_submit():
        if form.end_at.data and form.end_at.data < form.start_at.data:
            flash("End time must be >= start time", "danger")
            return render_template("bookings/booking_form.html", form=form, title="New Booking")

        b = VehicleBooking(
            vehicle_id=form.vehicle_id.data,
            employee_name=form.employee_name.data.strip(),
            department=(form.department.data or "").strip() or None,
            start_at=form.start_at.data,
            end_at=form.end_at.data,
            purpose=(form.purpose.data or "").strip() or None,
            status=BookingStatus.SCHEDULED,
        )
        db.session.add(b)
        db.session.commit()
        flash("Vehicle scheduled", "success")
        return redirect(url_for("bookings.booking_list"))

    return render_template("bookings/booking_form.html", form=form, title="New Booking")
