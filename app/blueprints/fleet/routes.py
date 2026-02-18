from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ...extensions import db
from ...models import Vehicle, Driver, Role
from ...rbac import role_required
from .forms import VehicleForm

bp = Blueprint("fleet", __name__, url_prefix="/fleet")


@bp.get("/vehicles")
@login_required
def vehicle_list():
    page = request.args.get("page", 1, type=int)
    vehicles = (
        Vehicle.query.options(selectinload(Vehicle.current_driver))
        .order_by(Vehicle.id.desc())
        .paginate(page=page, per_page=25, error_out=False)
    )
    return render_template("fleet/vehicles_list.html", vehicles=vehicles.items, pagination=vehicles)


# Backwards-compatible endpoint alias (some templates may reference fleet.vehicles_list)
bp.add_url_rule("/vehicles", endpoint="vehicles_list", view_func=vehicle_list, methods=["GET"])


def _driver_choices(form: VehicleForm):
    form.current_driver_id.choices = [(0, "--")]
    form.current_driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]


@bp.route("/vehicles/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def vehicle_create():
    form = VehicleForm(status="active", category="General")
    _driver_choices(form)

    if form.validate_on_submit():
        plate = form.plate_no.data.strip().upper()

        # Friendly uniqueness check before hitting DB constraint
        if Vehicle.query.filter_by(plate_no=plate).first():
            flash(f"Plate number '{plate}' already exists. Please use a unique plate.", "warning")
            return render_template("fleet/vehicle_form.html", form=form, title="New Vehicle")

        v = Vehicle(
            plate_no=plate,
            make_model=form.make_model.data.strip(),
            year=form.year.data,
            category=form.category.data,
            status=form.status.data.strip(),
            current_driver_id=(form.current_driver_id.data or 0) or None,
        )
        db.session.add(v)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Could not create vehicle. Plate '{plate}' already exists.", "danger")
            return render_template("fleet/vehicle_form.html", form=form, title="New Vehicle")

        flash("Vehicle created", "success")
        return redirect(url_for("fleet.vehicle_list"))
    return render_template("fleet/vehicle_form.html", form=form, title="New Vehicle")


@bp.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN)
def vehicle_edit(vehicle_id: int):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        flash("Vehicle not found", "warning")
        return redirect(url_for("fleet.vehicle_list"))

    form = VehicleForm(
        plate_no=v.plate_no,
        make_model=v.make_model,
        year=v.year,
        category=getattr(v, "category", "General"),
        status=v.status,
        current_driver_id=v.current_driver_id or 0,
    )
    _driver_choices(form)

    if form.validate_on_submit():
        new_plate = form.plate_no.data.strip().upper()

        # Prevent duplicate plate numbers on edit
        exists = Vehicle.query.filter(Vehicle.plate_no == new_plate, Vehicle.id != v.id).first()
        if exists:
            flash(f"Plate number '{new_plate}' already exists. Please use a unique plate.", "warning")
            return render_template("fleet/vehicle_form.html", form=form, title=f"Edit Vehicle #{v.id}")

        v.plate_no = new_plate
        v.make_model = form.make_model.data.strip()
        v.year = form.year.data
        v.category = form.category.data
        v.status = form.status.data.strip()
        v.current_driver_id = (form.current_driver_id.data or 0) or None

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(f"Could not update vehicle. Plate '{new_plate}' already exists.", "danger")
            return render_template("fleet/vehicle_form.html", form=form, title=f"Edit Vehicle #{v.id}")

        flash("Vehicle updated", "success")
        return redirect(url_for("fleet.vehicle_list"))

    return render_template("fleet/vehicle_form.html", form=form, title=f"Edit Vehicle #{v.id}")


@bp.post("/vehicles/<int:vehicle_id>/delete")
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN)
def vehicle_delete(vehicle_id: int):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        flash("Vehicle not found", "warning")
        return redirect(url_for("fleet.vehicle_list"))

    db.session.delete(v)
    db.session.commit()
    flash("Vehicle deleted", "success")
    return redirect(url_for("fleet.vehicle_list"))
