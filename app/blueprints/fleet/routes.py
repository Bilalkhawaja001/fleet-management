from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import Vehicle, Driver, Role
from ...rbac import role_required
from .forms import VehicleForm

bp = Blueprint("fleet", __name__, url_prefix="/fleet")


@bp.get("/vehicles")
@login_required
def vehicle_list():
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return render_template("fleet/vehicles_list.html", vehicles=vehicles)


def _driver_choices(form: VehicleForm):
    form.current_driver_id.choices = [(0, "--")]
    form.current_driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]


@bp.route("/vehicles/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def vehicle_create():
    form = VehicleForm(status="active")
    _driver_choices(form)

    if form.validate_on_submit():
        v = Vehicle(
            plate_no=form.plate_no.data.strip(),
            make_model=form.make_model.data.strip(),
            year=form.year.data,
            status=form.status.data.strip(),
            current_driver_id=(form.current_driver_id.data or 0) or None,
        )
        db.session.add(v)
        db.session.commit()
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
        status=v.status,
        current_driver_id=v.current_driver_id or 0,
    )
    _driver_choices(form)

    if form.validate_on_submit():
        v.plate_no = form.plate_no.data.strip()
        v.make_model = form.make_model.data.strip()
        v.year = form.year.data
        v.status = form.status.data.strip()
        v.current_driver_id = (form.current_driver_id.data or 0) or None
        db.session.commit()
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
