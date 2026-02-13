from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import FuelLog, Vehicle, Role
from ...rbac import role_required
from .forms import FuelLogForm

bp = Blueprint("fuel", __name__, url_prefix="/fuel")


def _vehicle_choices(form: FuelLogForm):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]


@bp.get("/")
@login_required
def fuel_list():
    logs = FuelLog.query.order_by(FuelLog.id.desc()).all()
    return render_template("fuel/fuel_list.html", logs=logs)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def fuel_create():
    form = FuelLogForm()
    _vehicle_choices(form)

    if form.validate_on_submit():
        log = FuelLog(
            vehicle_id=form.vehicle_id.data,
            liters=form.liters.data,
            amount=form.amount.data,
            odometer_km=form.odometer_km.data,
            vendor=(form.vendor.data or "").strip() or None,
            notes=(form.notes.data or "").strip() or None,
        )
        db.session.add(log)
        db.session.commit()
        flash("Fuel log added", "success")
        return redirect(url_for("fuel.fuel_list"))

    return render_template("fuel/fuel_form.html", form=form, title="New Fuel Log")
