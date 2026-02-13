from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from ...extensions import db
from ...models import (
    Driver,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    Role,
    Vehicle,
    WorkOrder,
    WorkOrderStatus,
    WorkOrderType,
    WorkSource,
)
from ...rbac import role_required
from .forms import IncidentDecisionForm, IncidentForm

bp = Blueprint("incidents", __name__, url_prefix="/incidents")


def _choices(form: IncidentForm):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]
    form.driver_id.choices = [(0, "--")]
    form.driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]


@bp.get("/")
@login_required
def incident_list():
    q = Incident.query
    open_only = (request.args.get("open") or "").strip()
    if open_only in {"1", "true", "yes"}:
        q = q.filter(Incident.status != IncidentStatus.CLOSED)

    rows = q.order_by(Incident.id.desc()).all()
    return render_template("incidents/incident_list.html", rows=rows, filter_open=open_only)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def incident_create():
    form = IncidentForm(incident_dt=datetime.now())
    _choices(form)

    if form.validate_on_submit():
        inc = Incident(
            incident_no=form.incident_no.data.strip(),
            vehicle_id=form.vehicle_id.data,
            driver_id=(form.driver_id.data or 0) or None,
            incident_dt=form.incident_dt.data,
            location=(form.location.data or "").strip() or None,
            incident_type=IncidentType(form.incident_type.data),
            severity=IncidentSeverity(form.severity.data),
            description=(form.description.data or "").strip() or None,
            status=IncidentStatus.PENDING_APPROVAL,
        )
        db.session.add(inc)
        db.session.commit()
        flash("Incident reported", "success")
        return redirect(url_for("incidents.incident_list"))

    return render_template("incidents/incident_form.html", form=form, title="New Incident")


@bp.route("/<int:incident_id>", methods=["GET", "POST"])
@login_required
def incident_detail(incident_id: int):
    inc = db.session.get(Incident, incident_id)
    if not inc:
        flash("Incident not found", "warning")
        return redirect(url_for("incidents.incident_list"))

    decision_form = IncidentDecisionForm()

    can_decide = current_user.role.value in [Role.SUPER_ADMIN.value, Role.ADMIN.value]

    if can_decide and decision_form.validate_on_submit():
        if decision_form.decision.data == "approve":
            inc.status = IncidentStatus.APPROVED
            inc.approver_user_id = current_user.id
            inc.approved_at = datetime.utcnow()
            inc.approval_note = (decision_form.note.data or "").strip() or None
            inc.reject_reason = None

            # Auto create Work Order for accident approval
            if inc.incident_type == IncidentType.ACCIDENT:
                wo = WorkOrder(
                    vehicle_id=inc.vehicle_id,
                    wo_type=WorkOrderType.ACCIDENT,
                    work_source=WorkSource.INTERNAL,
                    status=WorkOrderStatus.OPEN,
                    title=f"Accident Incident #{inc.incident_no}",
                    description=inc.description,
                )
                db.session.add(wo)

            db.session.commit()
            flash("Incident approved", "success")
        else:
            inc.status = IncidentStatus.REJECTED
            inc.approver_user_id = current_user.id
            inc.approved_at = datetime.utcnow()
            inc.reject_reason = (decision_form.note.data or "").strip() or "Rejected"
            db.session.commit()
            flash("Incident rejected", "success")

        return redirect(url_for("incidents.incident_detail", incident_id=inc.id))

    return render_template("incidents/incident_detail.html", inc=inc, decision_form=decision_form, can_decide=can_decide)
