from datetime import datetime, date, time

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from ...extensions import db
from ...models import FuelEntry, TripExpense, TripExpenseType, ItemsOwner, ItemsReturnStatus, Trip, TripStatus, UsageType, Vehicle, Driver, Role
from ...rbac import role_required
from .forms import TripForm
from .expense_forms import TripExpenseForm

bp = Blueprint("trips", __name__, url_prefix="/trips")


def _fill_choices(form: TripForm):
    form.vehicle_id.choices = [(0, "--")]
    form.vehicle_id.choices += [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]

    form.driver_id.choices = [(0, "--")]
    form.driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]


@bp.get("/")
@login_required
def trip_list():
    q = Trip.query

    # Filters
    status = (request.args.get("status") or "").strip()
    if status:
        try:
            q = q.filter(Trip.status == TripStatus(status))
        except Exception:
            pass

    day = (request.args.get("date") or "").strip()  # YYYY-MM-DD
    if day:
        try:
            d = date.fromisoformat(day)
            start_dt = datetime.combine(d, time.min)
            end_dt = datetime.combine(d, time.max)
            q = q.filter(Trip.time_out >= start_dt, Trip.time_out <= end_dt)
        except Exception:
            pass

    trips = q.order_by(Trip.id.desc()).all()
    return render_template(
        "trips/trips_list.html",
        trips=trips,
        filter_status=status,
        filter_date=day,
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def trip_create():
    form = TripForm(status=TripStatus.PLANNED.value)
    _fill_choices(form)

    if form.validate_on_submit():
        # Minimal conditional validation for items flow
        if form.carrying_items.data:
            if not (form.gatepass_no.data or "").strip():
                flash("Gatepass No is required when carrying items", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")
            if not (form.items_reason.data or "").strip():
                flash("Items reason is required when carrying items", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")
            if not (form.items_details.data or "").strip():
                flash("Items details are required when carrying items", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")

        # Trip completion requires closure fields
        if TripStatus(form.status.data) == TripStatus.COMPLETED:
            if form.odometer_start.data is None or form.odometer_end.data is None:
                flash("Start/End odometer are required to complete a trip", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")
            if form.time_out.data is None or form.time_in.data is None:
                flash("Time Out/Time In are required to complete a trip", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")
            if form.odometer_end.data < form.odometer_start.data:
                flash("End odometer must be >= start odometer", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")
            if form.time_in.data < form.time_out.data:
                flash("Time In must be >= Time Out", "danger")
                return render_template("trips/trip_form.html", form=form, title="New Trip")

        t = Trip(
            vehicle_id=(form.vehicle_id.data or 0) or None,
            driver_id=(form.driver_id.data or 0) or None,
            odometer_start=form.odometer_start.data,
            odometer_end=form.odometer_end.data,
            time_out=form.time_out.data,
            time_in=form.time_in.data,
            usage_type=UsageType(form.usage_type.data),
            department=(form.department.data or "").strip() or None,
            employee_name=(form.employee_name.data or "").strip() or None,
            origin=(form.origin.data or "").strip() or None,
            destination_city=(form.destination_city.data or "").strip() or None,
            destination=(form.destination.data or "").strip() or None,
            status=TripStatus(form.status.data),
            carrying_items=bool(form.carrying_items.data),
            items_owner=ItemsOwner(form.items_owner.data) if form.items_owner.data else None,
            gatepass_no=(form.gatepass_no.data or "").strip() or None,
            items_reason=(form.items_reason.data or "").strip() or None,
            items_details=(form.items_details.data or "").strip() or None,
            items_return_status=ItemsReturnStatus(form.items_return_status.data) if form.items_return_status.data else None,
            items_not_returned_reason=(form.items_not_returned_reason.data or "").strip() or None,
            items_expected_return_date=form.items_expected_return_date.data,
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
        odometer_start=t.odometer_start,
        odometer_end=t.odometer_end,
        time_out=t.time_out,
        time_in=t.time_in,
        usage_type=t.usage_type.value if t.usage_type else UsageType.OFFICIAL.value,
        department=t.department,
        employee_name=t.employee_name,
        origin=t.origin,
        destination_city=t.destination_city,
        destination=t.destination,
        status=t.status.value,
        carrying_items=t.carrying_items,
        items_owner=t.items_owner.value if t.items_owner else "",
        gatepass_no=t.gatepass_no,
        items_reason=t.items_reason,
        items_details=t.items_details,
        items_return_status=t.items_return_status.value if t.items_return_status else "",
        items_not_returned_reason=t.items_not_returned_reason,
        items_expected_return_date=t.items_expected_return_date,
        notes=t.notes,
    )
    _fill_choices(form)

    if form.validate_on_submit():
        if form.carrying_items.data:
            if not (form.gatepass_no.data or "").strip():
                flash("Gatepass No is required when carrying items", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
            if not (form.items_reason.data or "").strip():
                flash("Items reason is required when carrying items", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
            if not (form.items_details.data or "").strip():
                flash("Items details are required when carrying items", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")

        # Trip completion requires closure fields
        if TripStatus(form.status.data) == TripStatus.COMPLETED:
            if form.odometer_start.data is None or form.odometer_end.data is None:
                flash("Start/End odometer are required to complete a trip", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
            if form.time_out.data is None or form.time_in.data is None:
                flash("Time Out/Time In are required to complete a trip", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
            if form.odometer_end.data < form.odometer_start.data:
                flash("End odometer must be >= start odometer", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
            if form.time_in.data < form.time_out.data:
                flash("Time In must be >= Time Out", "danger")
                return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")

        t.vehicle_id = (form.vehicle_id.data or 0) or None
        t.driver_id = (form.driver_id.data or 0) or None
        t.odometer_start = form.odometer_start.data
        t.odometer_end = form.odometer_end.data
        t.time_out = form.time_out.data
        t.time_in = form.time_in.data
        t.usage_type = UsageType(form.usage_type.data)
        t.department = (form.department.data or "").strip() or None
        t.employee_name = (form.employee_name.data or "").strip() or None
        t.origin = (form.origin.data or "").strip() or None
        t.destination_city = (form.destination_city.data or "").strip() or None
        t.destination = (form.destination.data or "").strip() or None
        t.status = TripStatus(form.status.data)
        t.carrying_items = bool(form.carrying_items.data)
        t.items_owner = ItemsOwner(form.items_owner.data) if form.items_owner.data else None
        t.gatepass_no = (form.gatepass_no.data or "").strip() or None
        t.items_reason = (form.items_reason.data or "").strip() or None
        t.items_details = (form.items_details.data or "").strip() or None
        t.items_return_status = ItemsReturnStatus(form.items_return_status.data) if form.items_return_status.data else None
        t.items_not_returned_reason = (form.items_not_returned_reason.data or "").strip() or None
        t.items_expected_return_date = form.items_expected_return_date.data
        t.notes = (form.notes.data or "").strip() or None
        db.session.commit()
        flash("Trip updated", "success")
        return redirect(url_for("trips.trip_list"))

    return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")


@bp.get("/<int:trip_id>/expenses")
@login_required
def trip_expenses(trip_id: int):
    t = db.session.get(Trip, trip_id)
    if not t:
        flash("Trip not found", "warning")
        return redirect(url_for("trips.trip_list"))

    fuel_entries = FuelEntry.query.filter(FuelEntry.trip_id == t.id).order_by(FuelEntry.id.desc()).all()
    expenses = TripExpense.query.filter(TripExpense.trip_id == t.id).order_by(TripExpense.id.desc()).all()
    return render_template("trips/trip_expenses.html", trip=t, fuel_entries=fuel_entries, expenses=expenses)


@bp.route("/<int:trip_id>/expenses/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def trip_expense_create(trip_id: int):
    t = db.session.get(Trip, trip_id)
    if not t:
        flash("Trip not found", "warning")
        return redirect(url_for("trips.trip_list"))

    form = TripExpenseForm(expense_type=TripExpenseType.TOLL.value)
    if form.validate_on_submit():
        x = TripExpense(
            trip_id=t.id,
            expense_type=TripExpenseType(form.expense_type.data),
            expense_date=form.expense_date.data,
            amount=form.amount.data,
            description=(form.description.data or "").strip() or None,
        )
        db.session.add(x)
        db.session.commit()
        flash("Expense added", "success")
        return redirect(url_for("trips.trip_expenses", trip_id=t.id))

    return render_template("trips/trip_expense_form.html", trip=t, form=form)


@bp.post("/<int:trip_id>/delete")
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN)
def trip_delete(trip_id: int):
    t = db.session.get(Trip, trip_id)
    if not t:
        flash("Trip not found", "warning")
        return redirect(url_for("trips.trip_list"))

    db.session.delete(t)
    db.session.commit()
    flash("Trip deleted", "success")
    return redirect(url_for("trips.trip_list"))
