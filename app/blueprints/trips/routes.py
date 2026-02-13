from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import Trip, TripStatus, Vehicle, Driver, Role
from ...rbac import role_required
from .forms import TripForm

bp = Blueprint("trips", __name__, url_prefix="/trips")


def _fill_choices(form: TripForm):
    form.vehicle_id.choices = [(0, "--")]
    form.vehicle_id.choices += [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]

    form.driver_id.choices = [(0, "--")]
    form.driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]


@bp.get("/")
@login_required
def trip_list():
    trips = Trip.query.order_by(Trip.id.desc()).all()
    return render_template("trips/trips_list.html", trips=trips)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def trip_create():
    form = TripForm(status=TripStatus.PLANNED.value)
    _fill_choices(form)

    if form.validate_on_submit():
        t = Trip(
            vehicle_id=(form.vehicle_id.data or 0) or None,
            driver_id=(form.driver_id.data or 0) or None,
            origin=(form.origin.data or "").strip() or None,
            destination=(form.destination.data or "").strip() or None,
            status=TripStatus(form.status.data),
            notes=(form.notes.data or "").strip() or None,
        )
        db.session.add(t)
        db.session.commit()
        flash("Trip created", "success")
        return redirect(url_for("trips.trip_list"))

    return render_template("trips/trip_form.html", form=form, title="New Trip")


@bp.route("/<int:trip_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def trip_edit(trip_id: int):
    t = db.session.get(Trip, trip_id)
    if not t:
        flash("Trip not found", "warning")
        return redirect(url_for("trips.trip_list"))

    form = TripForm(
        vehicle_id=t.vehicle_id or 0,
        driver_id=t.driver_id or 0,
        origin=t.origin,
        destination=t.destination,
        status=t.status.value,
        notes=t.notes,
    )
    _fill_choices(form)

    if form.validate_on_submit():
        t.vehicle_id = (form.vehicle_id.data or 0) or None
        t.driver_id = (form.driver_id.data or 0) or None
        t.origin = (form.origin.data or "").strip() or None
        t.destination = (form.destination.data or "").strip() or None
        t.status = TripStatus(form.status.data)
        t.notes = (form.notes.data or "").strip() or None
        db.session.commit()
        flash("Trip updated", "success")
        return redirect(url_for("trips.trip_list"))

    return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
