from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from ...extensions import db
from ...models import Vehicle, PreventiveSchedule, WorkOrder, WorkOrderStatus, Part, Role
from ...rbac import role_required
from .forms import PreventiveScheduleForm, WorkOrderForm, WorkOrderStatusForm, PartForm

bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


def _vehicle_choices(form):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]


@bp.get("/schedules")
@login_required
def schedule_list():
    schedules = PreventiveSchedule.query.order_by(PreventiveSchedule.id.desc()).all()
    return render_template("maintenance/schedule_list.html", schedules=schedules)


@bp.route("/schedules/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def schedule_create():
    form = PreventiveScheduleForm()
    _vehicle_choices(form)

    if form.validate_on_submit():
        s = PreventiveSchedule(
            vehicle_id=form.vehicle_id.data,
            title=form.title.data.strip(),
            interval_km=form.interval_km.data,
            interval_days=form.interval_days.data,
        )
        db.session.add(s)
        db.session.commit()
        flash("Schedule created", "success")
        return redirect(url_for("maintenance.schedule_list"))

    return render_template("maintenance/schedule_form.html", form=form, title="New Preventive Schedule")


@bp.get("/work-orders")
@login_required
def wo_list():
    work_orders = WorkOrder.query.order_by(WorkOrder.id.desc()).all()
    return render_template("maintenance/wo_list.html", work_orders=work_orders)


@bp.route("/work-orders/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def wo_create():
    form = WorkOrderForm(status=WorkOrderStatus.OPEN.value)
    _vehicle_choices(form)

    if form.validate_on_submit():
        wo = WorkOrder(
            vehicle_id=form.vehicle_id.data,
            title=form.title.data.strip(),
            description=(form.description.data or "").strip() or None,
            status=WorkOrderStatus(form.status.data),
        )
        db.session.add(wo)
        db.session.commit()
        flash("Work order created", "success")
        return redirect(url_for("maintenance.wo_list"))

    return render_template("maintenance/wo_form.html", form=form, title="New Work Order")


@bp.route("/work-orders/<int:wo_id>", methods=["GET", "POST"])
@login_required
def wo_detail(wo_id: int):
    wo = db.session.get(WorkOrder, wo_id)
    if not wo:
        flash("Work order not found", "warning")
        return redirect(url_for("maintenance.wo_list"))

    part_form = PartForm()
    status_form = WorkOrderStatusForm(status=wo.status.value)

    # One page, two forms: use submit button name to route
    if part_form.submit.data and part_form.validate_on_submit():
        p = Part(
            work_order_id=wo.id,
            name=part_form.name.data.strip(),
            qty=part_form.qty.data,
            unit_cost=part_form.unit_cost.data,
        )
        db.session.add(p)
        db.session.commit()
        flash("Part added", "success")
        return redirect(url_for("maintenance.wo_detail", wo_id=wo.id))

    if status_form.submit.data and status_form.validate_on_submit():
        # Entry operator allowed to update status (no other edits here)
        wo.status = WorkOrderStatus(status_form.status.data)
        db.session.commit()
        flash("Status updated", "success")
        return redirect(url_for("maintenance.wo_detail", wo_id=wo.id))

    return render_template("maintenance/wo_detail.html", wo=wo, part_form=part_form, status_form=status_form)
