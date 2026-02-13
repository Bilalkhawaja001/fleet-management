from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from ...extensions import db
from ...models import Vehicle, VehicleDocument, VehicleDocStatus, VehicleDocType, Role
from ...rbac import role_required
from .forms import VehicleDocumentForm

bp = Blueprint("documents", __name__, url_prefix="/documents")


def _vehicle_choices(form: VehicleDocumentForm):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]


@bp.get("/")
@login_required
def doc_list():
    mode = (request.args.get("mode") or "").strip()  # expiring|expired|missing|all
    today = date.today()
    exp_window_end = today + timedelta(days=30)

    if mode == "missing":
        vehicles = Vehicle.query.order_by(Vehicle.plate_no).all()
        mandatory = [t for t in VehicleDocType]
        missing_rows = []
        for v in vehicles:
            active_types = {
                d.doc_type
                for d in (v.documents or [])
                if d.status == VehicleDocStatus.ACTIVE
            }
            missing = [t.value for t in mandatory if t not in active_types]
            if missing:
                missing_rows.append({"vehicle": v, "missing": missing})
        return render_template(
            "documents/doc_list.html",
            docs=[],
            mode=mode,
            today=today,
            exp_window_end=exp_window_end,
            missing_rows=missing_rows,
        )

    q = VehicleDocument.query
    if mode == "expiring":
        q = q.filter(
            VehicleDocument.status == VehicleDocStatus.ACTIVE,
            VehicleDocument.expiry_date >= today,
            VehicleDocument.expiry_date <= exp_window_end,
        )
    elif mode == "expired":
        q = q.filter(
            VehicleDocument.status == VehicleDocStatus.ACTIVE,
            VehicleDocument.expiry_date < today,
        )

    docs = q.order_by(VehicleDocument.expiry_date.asc(), VehicleDocument.id.desc()).all()
    return render_template(
        "documents/doc_list.html",
        docs=docs,
        mode=mode or "all",
        today=today,
        exp_window_end=exp_window_end,
        missing_rows=[],
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def doc_create():
    form = VehicleDocumentForm()
    _vehicle_choices(form)

    if form.validate_on_submit():
        # Enforce: only one ACTIVE per (vehicle_id, doc_type)
        VehicleDocument.query.filter_by(
            vehicle_id=form.vehicle_id.data,
            doc_type=VehicleDocType(form.doc_type.data),
            status=VehicleDocStatus.ACTIVE,
        ).update({"status": VehicleDocStatus.ARCHIVED})

        doc = VehicleDocument(
            vehicle_id=form.vehicle_id.data,
            doc_type=VehicleDocType(form.doc_type.data),
            doc_name=(form.doc_name.data or "").strip() or None,
            doc_number=(form.doc_number.data or "").strip() or None,
            issue_date=form.issue_date.data,
            expiry_date=form.expiry_date.data,
            status=VehicleDocStatus.ACTIVE,
        )
        db.session.add(doc)
        db.session.commit()
        flash("Document saved", "success")
        return redirect(url_for("documents.doc_list"))

    return render_template("documents/doc_form.html", form=form, title="New Vehicle Document")
