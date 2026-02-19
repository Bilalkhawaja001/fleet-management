from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_required
from werkzeug.utils import secure_filename

from ...extensions import db
from ...models import DocumentAttachment, Vehicle, VehicleDocument, VehicleDocStatus, VehicleDocType, Role, Trip
from ...rbac import role_required
from .forms import VehicleDocumentForm

bp = Blueprint("documents", __name__, url_prefix="/documents")


def _vehicle_choices(form: VehicleDocumentForm):
    form.vehicle_id.choices = [(v.id, f"{v.plate_no} - {v.make_model}") for v in Vehicle.query.order_by(Vehicle.plate_no).all()]
    form.trip_id.choices = [(0, "-- Optional --")]
    form.trip_id.choices += [(t.id, f"TRP-{t.id:05d} {t.origin or ''} -> {t.destination_city or t.destination or ''}") for t in Trip.query.order_by(Trip.id.desc()).limit(300).all()]


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


def _is_allowed_file(filename: str) -> bool:
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
    allowed = set(current_app.config.get("DOCUMENT_ALLOWED_EXTENSIONS", {"pdf", "jpg", "jpeg", "png", "webp"}))
    return ext in allowed


def _store_attachments(files, trip_id: int | None, vehicle_document_id: int):
    max_size_mb = int(current_app.config.get("DOCUMENT_MAX_FILE_SIZE_MB", 10))
    max_size_bytes = max_size_mb * 1024 * 1024
    base_rel = current_app.config.get("DOCUMENT_UPLOAD_BASE", "uploads/trips").strip("/\\")

    trip_folder = str(trip_id or "unlinked")
    upload_dir = Path(current_app.root_path).parent / base_rel / trip_folder
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        if not f or not getattr(f, "filename", None):
            continue

        original_name = f.filename
        safe_name = secure_filename(original_name)
        if not safe_name:
            raise ValueError("Invalid file name")
        if not _is_allowed_file(safe_name):
            raise ValueError(f"Unsupported file type for '{original_name}'")

        f.stream.seek(0, 2)
        size_bytes = f.stream.tell()
        f.stream.seek(0)

        if size_bytes > max_size_bytes:
            raise ValueError(f"'{original_name}' exceeds {max_size_mb}MB limit")

        stored_name = f"{uuid4().hex}_{safe_name}"
        file_path = upload_dir / stored_name
        f.save(file_path)

        rel_path = str((Path(base_rel) / trip_folder / stored_name).as_posix())
        saved.append(
            DocumentAttachment(
                vehicle_document_id=vehicle_document_id,
                original_filename=original_name,
                stored_filename=stored_name,
                storage_path=rel_path,
                mime_type=getattr(f, "mimetype", None),
                size_bytes=size_bytes,
            )
        )

    return saved


@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.ENTRY_OPERATOR)
def doc_create():
    form = VehicleDocumentForm()
    _vehicle_choices(form)

    if form.validate_on_submit():
        try:
            # Enforce: only one ACTIVE per (vehicle_id, doc_type)
            VehicleDocument.query.filter_by(
                vehicle_id=form.vehicle_id.data,
                doc_type=VehicleDocType(form.doc_type.data),
                status=VehicleDocStatus.ACTIVE,
            ).update({"status": VehicleDocStatus.ARCHIVED})

            doc = VehicleDocument(
                vehicle_id=form.vehicle_id.data,
                trip_id=(form.trip_id.data or 0) or None,
                doc_type=VehicleDocType(form.doc_type.data),
                doc_name=(form.doc_name.data or "").strip() or None,
                doc_number=(form.doc_number.data or "").strip() or None,
                issue_date=form.issue_date.data,
                expiry_date=form.expiry_date.data,
                status=VehicleDocStatus.ACTIVE,
            )
            db.session.add(doc)
            db.session.flush()

            upload_files = request.files.getlist("attachments")
            attachments = _store_attachments(upload_files, doc.trip_id, doc.id)
            for a in attachments:
                db.session.add(a)

            if attachments:
                doc.attachment_path = attachments[0].storage_path

            db.session.commit()
            flash(f"Document saved with {len(attachments)} attachment(s)", "success")
            return redirect(url_for("documents.doc_list"))
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception("Document save failed")
            flash(f"Document save failed: {exc}", "danger")

    return render_template("documents/doc_form.html", form=form, title="New Vehicle Document")
