from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import Driver, Role
from ...rbac import role_required
from .forms import DriverForm

bp = Blueprint("drivers", __name__, url_prefix="/drivers")


@bp.get("/")
@login_required
def driver_list():
    drivers = Driver.query.order_by(Driver.id.desc()).all()
    return render_template("drivers/drivers_list.html", drivers=drivers)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def driver_create():
    form = DriverForm(status="active")
    if form.validate_on_submit():
        d = Driver(
            name=form.name.data.strip(),
            phone=(form.phone.data or "").strip() or None,
            license_no=(form.license_no.data or "").strip() or None,
            license_expiry=form.license_expiry.data,
            status=form.status.data.strip(),
        )
        db.session.add(d)
        db.session.commit()
        flash("Driver created", "success")
        return redirect(url_for("drivers.driver_list"))
    return render_template("drivers/driver_form.html", form=form, title="New Driver")


@bp.route("/<int:driver_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN)
def driver_edit(driver_id: int):
    d = db.session.get(Driver, driver_id)
    if not d:
        flash("Driver not found", "warning")
        return redirect(url_for("drivers.driver_list"))

    form = DriverForm(obj=d)
    if form.validate_on_submit():
        d.name = form.name.data.strip()
        d.phone = (form.phone.data or "").strip() or None
        d.license_no = (form.license_no.data or "").strip() or None
        d.license_expiry = form.license_expiry.data
        d.status = form.status.data.strip()
        db.session.commit()
        flash("Driver updated", "success")
        return redirect(url_for("drivers.driver_list"))

    return render_template("drivers/driver_form.html", form=form, title=f"Edit Driver #{d.id}")


@bp.post("/<int:driver_id>/delete")
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN)
def driver_delete(driver_id: int):
    d = db.session.get(Driver, driver_id)
    if not d:
        flash("Driver not found", "warning")
        return redirect(url_for("drivers.driver_list"))

    db.session.delete(d)
    db.session.commit()
    flash("Driver deleted", "success")
    return redirect(url_for("drivers.driver_list"))
