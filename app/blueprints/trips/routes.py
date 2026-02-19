from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from ...extensions import db
from ...models import FuelEntry, FuelEntryStatus, Role, Trip, TripExpense, TripExpenseType, TripItem, ItemOwnership, ItemUom, ItemReturnType, TripStatus, UsageType, Vehicle, Driver
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
    return {TripStatus.PLANNED, TripStatus.ASSIGNED, TripStatus.IN_TRANSIT}


def _parse_trip_items_or_error():
    item_ownerships = request.form.getlist("item_ownership[]")
    item_gatepass = request.form.getlist("item_gatepass_no[]")
    item_depts = request.form.getlist("item_department[]")
    item_descs = request.form.getlist("item_description[]")
    item_qtys = request.form.getlist("item_qty[]")
    item_uoms = request.form.getlist("item_uom[]")
    item_dests = request.form.getlist("item_destination[]")
    item_returns = request.form.getlist("item_return_type[]")
    item_notes = request.form.getlist("item_notes[]")

    rows = []
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
            return None, f"Ownership is required at item row {i + 1}"
        if not desc:
            return None, f"Item description is required at item row {i + 1}"
        if not qty_raw:
            return None, f"Qty is required at item row {i + 1}"
        try:
            qty = Decimal(qty_raw)
        except Exception:
            return None, f"Qty is invalid at item row {i + 1}"
        if qty <= 0:
            return None, f"Qty must be > 0 at item row {i + 1}"
        if uom not in {e.value for e in ItemUom}:
            return None, f"UoM is required at item row {i + 1}"
        if not dest:
            return None, f"Destination is required at item row {i + 1}"
        if return_type not in {e.value for e in ItemReturnType}:
            return None, f"Return type is required at item row {i + 1}"

        if ownership == ItemOwnership.COMPANY.value:
            if not gatepass:
                return None, f"Gatepass No is required for company item at row {i + 1}"
            if not dept:
                return None, f"Department is required for company item at row {i + 1}"

        rows.append(
            {
                "ownership": ItemOwnership(ownership),
                "gatepass_no": gatepass or None,
                "department": dept or None,
                "item_description": desc,
                "qty": qty,
                "uom": ItemUom(uom),
                "destination": dest,
                "return_type": ItemReturnType(return_type),
                "notes": notes or None,
            }
        )

    return rows, None


def _parse_trip_fuel_rows_or_error():
    fuel_datetimes = request.form.getlist("fuel_datetime[]")
    fuel_types = request.form.getlist("fuel_type[]")
    liters_values = request.form.getlist("fuel_liters[]")
    rate_values = request.form.getlist("fuel_rate[]")
    amount_values = request.form.getlist("fuel_amount[]")
    notes_values = request.form.getlist("fuel_notes[]")

    rows = []
    fuel_row_count = max(
        len(fuel_datetimes), len(fuel_types), len(liters_values), len(rate_values), len(amount_values), len(notes_values)
    )

    for i in range(fuel_row_count):
        dt_raw = (fuel_datetimes[i] if i < len(fuel_datetimes) else "").strip()
        fuel_type = (fuel_types[i] if i < len(fuel_types) else "").strip().lower()
        liters_raw = (liters_values[i] if i < len(liters_values) else "").strip()
        rate_raw = (rate_values[i] if i < len(rate_values) else "").strip()
        amount_raw = (amount_values[i] if i < len(amount_values) else "").strip()
        notes_raw = (notes_values[i] if i < len(notes_values) else "").strip()

        if not any([dt_raw, fuel_type, liters_raw, rate_raw, amount_raw, notes_raw]):
            continue

        if not liters_raw:
            return None, f"Liters are required at fuel row {i + 1}"

        try:
            liters = Decimal(liters_raw)
        except InvalidOperation:
            return None, f"Invalid liters at fuel row {i + 1}"

        if liters <= 0:
            return None, f"Liters must be > 0 at fuel row {i + 1}"

        rate = None
        if rate_raw:
            try:
                rate = Decimal(rate_raw)
            except InvalidOperation:
                return None, f"Invalid rate at fuel row {i + 1}"
            if rate < 0:
                return None, f"Rate must be >= 0 at fuel row {i + 1}"

        amount = None
        if amount_raw:
            try:
                amount = Decimal(amount_raw)
            except InvalidOperation:
                return None, f"Invalid amount at fuel row {i + 1}"
            if amount < 0:
                return None, f"Amount must be >= 0 at fuel row {i + 1}"

        if amount is None and rate is not None:
            amount = (rate * liters).quantize(Decimal("0.01"))

        try:
            fuel_dt = datetime.fromisoformat(dt_raw) if dt_raw else datetime.now()
        except ValueError:
            return None, f"Invalid fuel date/time at row {i + 1}"

        rows.append(
            {
                "fuel_datetime": fuel_dt,
                "fuel_type": fuel_type,
                "liters": liters,
                "rate": rate,
                "amount": amount,
                "notes": notes_raw,
            }
        )

    return rows, None


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
    form = TripForm(status=TripStatus.PLANNED.value, usage_type=UsageType.OFFICIAL.value, department="Centralized", origin="Nooriabad")
    _fill_choices(form)

    if form.validate_on_submit():
        if (form.vehicle_id.data or 0) == 0:
            flash("Vehicle is required", "danger")
            return render_template("trips/trip_form.html", form=form, title="Quick Trip")

        item_rows, item_err = _parse_trip_items_or_error()
        if item_err:
            flash(item_err, "danger")
            return render_template("trips/trip_form.html", form=form, title="Quick Trip")

        fuel_rows, fuel_err = _parse_trip_fuel_rows_or_error()
        if fuel_err:
            flash(fuel_err, "danger")
            return render_template("trips/trip_form.html", form=form, title="Quick Trip")

        t = Trip(
            vehicle_id=form.vehicle_id.data,
            driver_id=(form.driver_id.data or 0) or None,
            odometer_start=form.odometer_start.data,
            time_out=form.time_out.data,
            usage_type=UsageType(form.usage_type.data).value,
            department=(form.department.data or "").strip(),
            employee_name=(form.employee_name.data or "").strip(),
            origin=(form.origin.data or "").strip(),
            destination_city=(form.destination_city.data or "").strip(),
            destination=(form.destination.data or "").strip(),
            status=TripStatus(form.status.data),
            notes=(form.notes.data or "").strip() or None,
        )
        db.session.add(t)
        db.session.flush()

        for row in item_rows:
            db.session.add(TripItem(trip_id=t.id, **row))

        for idx, row in enumerate(fuel_rows, start=1):
            fuel_note_parts = []
            if row["fuel_type"]:
                fuel_note_parts.append(f"Fuel Type: {row['fuel_type'].title()}")
            if row["notes"]:
                fuel_note_parts.append(row["notes"])
            fuel_notes = " | ".join(fuel_note_parts) if fuel_note_parts else None

            db.session.add(
                FuelEntry(
                    vehicle_id=t.vehicle_id,
                    driver_id=t.driver_id,
                    trip_id=t.id,
                    slip_no=f"TRIP-{t.id}-{idx}-{int(row['fuel_datetime'].timestamp())}",
                    fuel_date=row["fuel_datetime"].date(),
                    liters=row["liters"],
                    rate=row["rate"],
                    amount=row["amount"],
                    fuel_purpose=(t.usage_type.value if hasattr(t.usage_type, "value") else str(t.usage_type or UsageType.OFFICIAL.value)),
                    status=FuelEntryStatus.PENDING,
                    reject_reason=fuel_notes,
                )
            )

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
        usage_type=(t.usage_type if isinstance(t.usage_type, str) else (t.usage_type.value if t.usage_type else UsageType.OFFICIAL.value)),
        department=t.department or "Centralized",
        employee_name=t.employee_name,
        origin=t.origin or "Nooriabad",
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
        # Driver is optional in merged trip workflow.

        item_rows, item_err = _parse_trip_items_or_error()
        if item_err:
            flash(item_err, "danger")
            return render_template("trips/trip_form.html", form=form, title=f"Edit Trip #{t.id}")

        t.vehicle_id = form.vehicle_id.data
        t.driver_id = (form.driver_id.data or 0) or None
        t.odometer_start = form.odometer_start.data
        t.time_out = form.time_out.data
        t.usage_type = UsageType(form.usage_type.data).value
        t.department = (form.department.data or "").strip()
        t.employee_name = (form.employee_name.data or "").strip()
        t.origin = (form.origin.data or "").strip()
        t.destination_city = (form.destination_city.data or "").strip()
        t.destination = (form.destination.data or "").strip()
        t.status = TripStatus(form.status.data)
        t.notes = (form.notes.data or "").strip() or None

        TripItem.query.filter(TripItem.trip_id == t.id).delete()
        for row in item_rows:
            db.session.add(TripItem(trip_id=t.id, **row))

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

    has_returnable_items = any(getattr(i.return_type, 'value', i.return_type) == ItemReturnType.RETURNABLE.value for i in (t.trip_items or []))
    return_confirm = (request.form.get("return_confirmation") or "").strip().lower() in {"1", "true", "yes", "on"}
    if has_returnable_items and not return_confirm:
        msg = "Please confirm returnable items status before ending trip"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("trips.trip_list"))

    t.end_time = form.end_time.data
    t.time_in = form.end_time.data
    t.end_odometer = end_odometer
    t.odometer_end = end_odometer
    t.running_km = max(0, end_odometer - start_odometer)
    t.status = TripStatus.COMPLETED
    if form.notes.data:
        existing = (t.notes or "").strip()
        t.notes = f"{existing}\n{form.notes.data.strip()}".strip() if existing else form.notes.data.strip()

    t.returnable_items_confirmed = bool(return_confirm)
    t.returnable_items_confirmed_at = datetime.utcnow() if return_confirm else None

    for x in expense_items:
        db.session.add(x)

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
                "returnable_items_confirmed": t.returnable_items_confirmed,
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

    try:
        # Break FK dependencies first for safe delete
        FuelEntry.query.filter(FuelEntry.trip_id == t.id).update({FuelEntry.trip_id: None}, synchronize_session=False)
        TripExpense.query.filter(TripExpense.trip_id == t.id).delete(synchronize_session=False)
        TripItem.query.filter(TripItem.trip_id == t.id).delete(synchronize_session=False)

        db.session.delete(t)
        db.session.commit()
        flash("Trip deleted", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Trip could not be deleted: {exc}", "danger")

    return redirect(url_for("trips.trip_list"))
