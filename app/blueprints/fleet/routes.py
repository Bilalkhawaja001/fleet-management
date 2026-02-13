from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import Vehicle, Role
from ...rbac import role_required
from .forms import VehicleForm

bp = Blueprint("fleet", __name__, url_prefix="/fleet")


@bp.get("/vehicles")
@login_required
def vehicle_list():
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return render_template("fleet/vehicles_list.html", vehicles=vehicles)


@bp.route("/vehicles/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def vehicle_create():
    form = VehicleForm(status="active")
    if form.validate_on_submit():
        v = Vehicle(
            plate_no=form.plate_no.data.strip(),
            make_model=form.make_model.data.strip(),
            year=form.year.data,
            status=form.status.data.strip(),
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

    form = VehicleForm(obj=v)
    if form.validate_on_submit():
        v.plate_no = form.plate_no.data.strip()
        v.make_model = form.make_model.data.strip()
        v.year = form.year.data
        v.status = form.status.data.strip()
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
