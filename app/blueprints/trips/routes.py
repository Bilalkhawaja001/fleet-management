from datetime import date, datetime, time
from decimal import Decimal

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from ...extensions import db
from ...models import FuelEntry, Role, Trip, TripExpense, TripExpenseType, TripItem, ItemOwnership, ItemUom, ItemReturnType, TripStatus, UsageType, Vehicle, Driver
from ...rbac import role_required
from .expense_forms import TripExpenseForm
from .forms import EndTripForm, TripForm

bp = Blueprint("trips", __name__, url_prefix="/trips")


def _fill_choices(form: TripForm):
    form.vehicle_id.choices = [(0, "-- Select Vehicle --")]
    form.vehicle_id.choices += [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]

    form.driver_id.choices = [(0, "-- Select Driver --")]
    form.driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]


def _editable_statuses():
    return {TripStatus.ASSIGNED, TripStatus.IN_TRANSIT}


@bp.get("/")
@login_required
def trip_list():
    q = Trip.query

    status = (request.args.get("status") or "").strip()
    if status:
        try:
            q = q.filter(Trip.status == TripStatus(status))
        except ValueError:
            flash("Invalid status filter ignored", "warning")

    day = (request.args.get("date") or "").strip()
    if day:
        try:
            d = date.fromisoformat(day)
            start_dt = datetime.combine(d, time.min)
            end_dt = datetime.combine(d, time.max)
            q = q.filter(Trip.time_out >= start_dt, Trip.time_out <= end_dt)
        except ValueError:
            flash("Invalid date filter ignored", "warning")

    trips = q.order_by(Trip.id.desc()).all()
    end_form = EndTripForm()
    end_form.set_default_now()
    return render_template("trips/trips_list.html", trips=trips, filter_status=status, filter_date=day, end_form=end_form)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def trip_create():
    form = TripForm(status=TripStatus.PLANNED.value, usage_type=UsageType.OFFICIAL.value)
    _fill_choices(form)

    if form.validate_on_submit():
        if (form.vehicle_id.data or 0) == 0:
            flash("Vehicle is required", "danger")
            return render_template("trips/trip_form.html", form=form, title="Quick Trip")
        if (form.driver_id.data or 0) == 0:
            flash("Driver is required", "danger")
            return render_template("trips/trip_form.html", form=form, title="Quick Trip")

        t = Trip(
            vehicle_id=form.vehicle_id.data,
            driver_id=form.driver_id.data,
            odometer_start=form.odometer_start.data,
            time_out=form.time_out.data,
            usage_type=UsageType(form.usage_type.data),
            department=(form.department.data or "").strip(),
            employee_name=(form.employee_name.data or "").strip(),
            origin=(form.origin.data or "").strip(),
            destination_city=(form.destination_city.data or "").strip(),
            destination=(form.destination.data or "").strip(),
            status=TripStatus(form.status.data),
            notes=(form.notes.data or "").strip() or None,
        )
        db.session.add(t)
        db.session.commit()
        flash("Trip saved", "success")
        return redirect(url_for("trips.trip_list"))

    return render_template("trips/trip_form.html", form=form, title="Quick Trip")


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
        time_out=t.time_out,
        usage_type=t.usage_type.value if t.usage_type else UsageType.OFFICIAL.value,
        department=t.department,
        employee_name=t.employee_name,
        origin=t.origin,
        destination_city=t.destination_city,
        destination=t.destination,
        status=t.status.value,
        notes=t.notes,
    )
    _fill_choices(form)

    if form.validate_on_submit():
        if (form.vehicle_id.data or 0) == 0:
            flash("Vehicle is required", "danger")
            return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")
        if (form.driver_id.data or 0) == 0:
            flash("Driver is required", "danger")
            return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")

        t.vehicle_id = form.vehicle_id.data
        t.driver_id = form.driver_id.data
        t.odometer_start = form.odometer_start.data
        t.time_out = form.time_out.data
        t.usage_type = UsageType(form.usage_type.data)
        t.department = (form.department.data or "").strip()
        t.employee_name = (form.employee_name.data or "").strip()
        t.origin = (form.origin.data or "").strip()
        t.destination_city = (form.destination_city.data or "").strip()
        t.destination = (form.destination.data or "").strip()
        t.status = TripStatus(form.status.data)
        t.notes = (form.notes.data or "").strip() or None
        db.session.commit()
        flash("Trip updated", "success")
        return redirect(url_for("trips.trip_list"))

    return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")


@bp.post("/<int:trip_id>/end")
@bp.post("/<int:trip_id>/end-plus")
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def trip_end(trip_id: int):
    t = db.session.get(Trip, trip_id)
    if not t:
        flash("Trip not found", "warning")
        return redirect(url_for("trips.trip_list"))

    if t.status not in _editable_statuses():
        msg = "Only Assigned / In Transit trips can be ended"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("trips.trip_list"))

    form = EndTripForm()
    if not form.validate_on_submit():
        msg = "End date/time and end odometer are required"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("trips.trip_list"))

    end_odometer = form.end_odometer.data
    start_odometer = t.odometer_start or 0
    if end_odometer < start_odometer:
        msg = "End odometer must be >= start odometer"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("trips.trip_list"))

    # Expenses from repeatable rows
    expense_types = request.form.getlist("expense_type[]")
    expense_amounts = request.form.getlist("expense_amount[]")
    expense_remarks = request.form.getlist("expense_remarks[]")

    expense_items: list[TripExpense] = []
    exp_row_count = max(len(expense_types), len(expense_amounts), len(expense_remarks))
    for i in range(exp_row_count):
        et = (expense_types[i] if i < len(expense_types) else "").strip().lower()
        amt_raw = (expense_amounts[i] if i < len(expense_amounts) else "").strip()
        rem = (expense_remarks[i] if i < len(expense_remarks) else "").strip()

        if not et and not amt_raw and not rem:
            continue
        if et not in {e.value for e in TripExpenseType}:
            msg = f"Invalid expense type at row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))
        if not amt_raw:
            msg = f"Amount is required at expense row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))
        try:
            amt = Decimal(amt_raw)
        except Exception:
            msg = f"Invalid amount at expense row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))
        if amt < 0:
            msg = f"Amount must be >= 0 at expense row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        expense_items.append(
            TripExpense(
                trip_id=t.id,
                expense_type=TripExpenseType(et),
                amount=amt,
                description=rem or None,
                expense_date=(form.end_time.data.date() if form.end_time.data else None),
            )
        )

    # Carrying items rows
    item_ownerships = request.form.getlist("item_ownership[]")
    item_gatepass = request.form.getlist("item_gatepass_no[]")
    item_depts = request.form.getlist("item_department[]")
    item_descs = request.form.getlist("item_description[]")
    item_qtys = request.form.getlist("item_qty[]")
    item_uoms = request.form.getlist("item_uom[]")
    item_dests = request.form.getlist("item_destination[]")
    item_returns = request.form.getlist("item_return_type[]")
    item_notes = request.form.getlist("item_notes[]")

    trip_items: list[TripItem] = []
    item_row_count = max(
        len(item_ownerships), len(item_gatepass), len(item_depts), len(item_descs), len(item_qtys), len(item_uoms), len(item_dests), len(item_returns), len(item_notes)
    )

    for i in range(item_row_count):
        ownership = (item_ownerships[i] if i < len(item_ownerships) else "").strip().lower()
        gatepass = (item_gatepass[i] if i < len(item_gatepass) else "").strip()
        dept = (item_depts[i] if i < len(item_depts) else "").strip()
        desc = (item_descs[i] if i < len(item_descs) else "").strip()
        qty_raw = (item_qtys[i] if i < len(item_qtys) else "").strip()
        uom = (item_uoms[i] if i < len(item_uoms) else "").strip().lower()
        dest = (item_dests[i] if i < len(item_dests) else "").strip()
        return_type = (item_returns[i] if i < len(item_returns) else "").strip().lower()
        notes = (item_notes[i] if i < len(item_notes) else "").strip()

        if not any([ownership, gatepass, dept, desc, qty_raw, uom, dest, return_type, notes]):
            continue

        if ownership not in {e.value for e in ItemOwnership}:
            msg = f"Ownership is required at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        if not desc:
            msg = f"Item description is required at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        if not qty_raw:
            msg = f"Qty is required at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))
        try:
            qty = Decimal(qty_raw)
        except Exception:
            msg = f"Qty is invalid at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))
        if qty <= 0:
            msg = f"Qty must be > 0 at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        if uom not in {e.value for e in ItemUom}:
            msg = f"UoM is required at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        if not dest:
            msg = f"Destination is required at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        if return_type not in {e.value for e in ItemReturnType}:
            msg = f"Return type is required at item row {i + 1}"
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("trips.trip_list"))

        if ownership == ItemOwnership.COMPANY.value:
            if not gatepass:
                msg = f"Gatepass No is required for company item at row {i + 1}"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"ok": False, "error": msg}), 400
                flash(msg, "danger")
                return redirect(url_for("trips.trip_list"))
            if not dept:
                msg = f"Department is required for company item at row {i + 1}"
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"ok": False, "error": msg}), 400
                flash(msg, "danger")
                return redirect(url_for("trips.trip_list"))

        trip_items.append(
            TripItem(
                trip_id=t.id,
                ownership=ItemOwnership(ownership),
                gatepass_no=(gatepass or None),
                department=(dept or None),
                item_description=desc,
                qty=qty,
                uom=ItemUom(uom),
                destination=dest,
                return_type=ItemReturnType(return_type),
                notes=(notes or None),
            )
        )

    t.end_time = form.end_time.data
    t.time_in = form.end_time.data
    t.end_odometer = end_odometer
    t.odometer_end = end_odometer
    t.running_km = max(0, end_odometer - start_odometer)
    t.status = TripStatus.COMPLETED
    if form.notes.data:
        existing = (t.notes or "").strip()
        t.notes = f"{existing}\n{form.notes.data.strip()}".strip() if existing else form.notes.data.strip()

    for x in expense_items:
        db.session.add(x)
    for it in trip_items:
        db.session.add(it)

    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "ok": True,
                "trip_id": t.id,
                "status": t.status.value,
                "end_time": t.end_time.strftime("%Y-%m-%d %H:%M") if t.end_time else "",
                "end_odometer": t.end_odometer,
                "running_km": t.running_km,
                "items_saved": len(trip_items),
            }
        )

    flash("Trip ended successfully", "success")
    return redirect(url_for("trips.trip_list"))


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
