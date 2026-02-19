import csv
import io
from datetime import datetime, date, time
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, render_template, Response, send_file, request
from flask_login import login_required
from werkzeug.utils import secure_filename

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from ...models import Trip, FuelEntry, FuelPurpose, WorkOrder, Vehicle, Driver, PreventiveSchedule
from .forms import DateRangeForm

bp = Blueprint("reports", __name__, url_prefix="/reports")


def _enum_value(value, default=""):
    if value is None:
        return default
    return getattr(value, "value", value)


def _validate_report_upload(file_storage):
    if not file_storage or not getattr(file_storage, "filename", None):
        return None, None

    safe_name = secure_filename(file_storage.filename)
    if not safe_name:
        raise ValueError("Invalid upload filename")

    ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
    allowed = {"pdf", "csv", "jpg", "jpeg", "png", "webp"}
    if ext not in allowed:
        raise ValueError("Unsupported upload type. Allowed: pdf,csv,jpg,jpeg,png,webp")

    max_size_mb = 10
    max_size_bytes = max_size_mb * 1024 * 1024
    file_storage.stream.seek(0, 2)
    size_bytes = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size_bytes > max_size_bytes:
        raise ValueError(f"Upload exceeds {max_size_mb}MB limit")

    upload_dir = Path(current_app.root_path).parent / "uploads" / "reports"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}_{safe_name}"
    out_path = upload_dir / stored_name
    file_storage.save(out_path)
    return safe_name, str(out_path)


def _parse_date_range():
    form = DateRangeForm(request.args)

    # vehicle dropdown choices
    form.vehicle_id.choices = [(0, "All")]
    form.vehicle_id.choices += [(v.id, v.plate_no) for v in Vehicle.query.order_by(Vehicle.plate_no).all()]

    # driver dropdown choices
    form.driver_id.choices = [(0, "All")]
    form.driver_id.choices += [(d.id, d.name) for d in Driver.query.order_by(Driver.name).all()]

    # Default: date-to-date = Today..Today
    if not request.args.get("start_date") and not request.args.get("end_date"):
        today = date.today()
        form.start_date.data = today
        form.end_date.data = today

    start_dt = end_dt = None
    if form.start_date.data:
        start_dt = datetime.combine(form.start_date.data, time.min)
    if form.end_date.data:
        end_dt = datetime.combine(form.end_date.data, time.max)

    vehicle_id = (form.vehicle_id.data or 0) or 0
    if vehicle_id == 0:
        vehicle_id = None

    driver_id = (form.driver_id.data or 0) or 0
    if driver_id == 0:
        driver_id = None

    fuel_purpose_raw = (form.fuel_purpose.data or "").strip().lower()
    allowed_purpose = {p.value for p in FuelPurpose}
    fuel_purpose = fuel_purpose_raw if fuel_purpose_raw in allowed_purpose else None

    return form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form, _, _, _, _, _ = _parse_date_range()

    if request.method == "POST":
        try:
            upload = request.files.get("report_file") or request.files.get("file")
            original_name, stored_path = _validate_report_upload(upload)
            if original_name:
                flash(f"Report upload received: {original_name}", "success")
                current_app.logger.info("Report upload saved", extra={"filename": original_name, "path": stored_path})
            else:
                flash("No file selected. Filters are still applied.", "info")
        except Exception as exc:
            current_app.logger.exception("Reports upload failed")
            flash(f"Report upload failed: {exc}", "danger")

    return render_template("reports/index.html", form=form)


def _csv_response(filename: str, rows, header):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for r in rows:
        writer.writerow(r)

    out = buf.getvalue()
    return Response(
        out,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _pdf_simple_table(filename: str, title: str, header, rows, subtitle: str | None = None, *, landscape_mode: bool = True):
    packet = io.BytesIO()

    page_size = landscape(A4) if landscape_mode else A4
    c = canvas.Canvas(packet, pagesize=page_size)
    width, height = page_size

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title)

    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if subtitle:
        y -= 14
        c.drawString(40, y, subtitle)

    y -= 25
    c.setFont("Helvetica-Bold", 9)
    x = 40
    col_width = (width - 80) / max(1, len(header))
    for i, h in enumerate(header):
        c.drawString(x + i * col_width, y, str(h)[:25])

    y -= 15
    c.setFont("Helvetica", 9)
    for row in rows:
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)
        for i, val in enumerate(row):
            c.drawString(x + i * col_width, y, str(val)[:25])
        y -= 14

    c.save()
    packet.seek(0)
    return send_file(packet, as_attachment=True, download_name=filename, mimetype="application/pdf")


def _subtitle(form: DateRangeForm):
    s = form.start_date.data.isoformat() if form.start_date.data else ""
    e = form.end_date.data.isoformat() if form.end_date.data else ""
    v = ""
    d = ""
    if form.vehicle_id.data and int(form.vehicle_id.data) != 0:
        veh = Vehicle.query.get(int(form.vehicle_id.data))
        v = f" vehicle={veh.plate_no}" if veh else ""
    if form.driver_id.data and int(form.driver_id.data) != 0:
        dr = Driver.query.get(int(form.driver_id.data))
        d = f" driver={dr.name}" if dr else ""
    p = f" fuel_purpose={form.fuel_purpose.data}" if getattr(form, 'fuel_purpose', None) and form.fuel_purpose.data else ""
    return f"Range: {s}..{e}{v}{d}{p}".strip()


@bp.get("/trips.csv")
@login_required
def trips_csv():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = Trip.query
    if start_dt:
        q = q.filter(Trip.created_at >= start_dt)
    if end_dt:
        q = q.filter(Trip.created_at <= end_dt)
    if vehicle_id:
        q = q.filter(Trip.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)

    trips = q.order_by(Trip.id.desc()).all()
    rows = []
    for t in trips:
        route = " -> ".join([p for p in [t.origin or "", t.destination_city or "", t.destination or ""] if p])
        rows.append(
            [
                t.id,
                t.status.value,
                _enum_value(t.usage_type, ""),
                t.vehicle.plate_no if t.vehicle else "",
                t.driver.name if t.driver else "",
                t.time_out.strftime("%Y-%m-%d %H:%M") if t.time_out else "",
                t.time_in.strftime("%Y-%m-%d %H:%M") if t.time_in else "",
                t.odometer_start or "",
                t.odometer_end or "",
                t.distance_km or "",
                f"{t.fuel_liters:.2f}" if t.fuel_liters else "",
                f"{t.fuel_amount:.2f}" if t.fuel_amount else "",
                f"{t.toll_amount:.2f}" if t.toll_amount else "",
                f"{t.other_amount:.2f}" if t.other_amount else "",
                f"{t.total_expenses:.2f}" if t.total_expenses else "",
                f"{t.fuel_avg_km_per_l:.2f}" if t.fuel_avg_km_per_l else "",
                route,
            ]
        )
    return _csv_response(
        "trips.csv",
        rows,
        [
            "trip_id",
            "status",
            "usage_type",
            "vehicle",
            "driver",
            "time_out",
            "time_in",
            "start_odo",
            "end_odo",
            "distance_km",
            "fuel_liters",
            "fuel_amount",
            "toll_amount",
            "other_amount",
            "total_expenses",
            "fuel_avg_km_per_l",
            "route",
        ],
    )


@bp.get("/trips.pdf")
@login_required
def trips_pdf():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = Trip.query
    if start_dt:
        q = q.filter(Trip.created_at >= start_dt)
    if end_dt:
        q = q.filter(Trip.created_at <= end_dt)
    if vehicle_id:
        q = q.filter(Trip.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)

    trips = q.order_by(Trip.id.desc()).all()
    rows = []
    for t in trips:
        route = " -> ".join([p for p in [t.origin or "", t.destination_city or "", t.destination or ""] if p])
        rows.append(
            [
                t.id,
                t.status.value,
                _enum_value(t.usage_type, ""),
                t.vehicle.plate_no if t.vehicle else "",
                t.driver.name if t.driver else "",
                t.time_out.strftime("%Y-%m-%d %H:%M") if t.time_out else "",
                t.time_in.strftime("%Y-%m-%d %H:%M") if t.time_in else "",
                t.odometer_start or "",
                t.odometer_end or "",
                t.distance_km or "",
                f"{t.fuel_liters:.2f}" if t.fuel_liters else "",
                f"{t.fuel_amount:.2f}" if t.fuel_amount else "",
                f"{t.toll_amount:.2f}" if t.toll_amount else "",
                f"{t.other_amount:.2f}" if t.other_amount else "",
                f"{t.total_expenses:.2f}" if t.total_expenses else "",
                f"{t.fuel_avg_km_per_l:.2f}" if t.fuel_avg_km_per_l else "",
                route,
            ]
        )
    return _pdf_simple_table(
        "trips.pdf",
        "Trips Report",
        [
            "trip_id",
            "status",
            "usage_type",
            "vehicle",
            "driver",
            "time_out",
            "time_in",
            "start_odo",
            "end_odo",
            "distance_km",
            "fuel_liters",
            "fuel_amount",
            "toll_amount",
            "other_amount",
            "total_expenses",
            "fuel_avg_km_per_l",
            "route",
        ],
        rows,
        subtitle=_subtitle(form),
        landscape_mode=True,
    )


@bp.get("/fuel.csv")
@login_required
def fuel_csv():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = FuelEntry.query
    if start_dt:
        q = q.filter(FuelEntry.created_at >= start_dt)
    if end_dt:
        q = q.filter(FuelEntry.created_at <= end_dt)
    if vehicle_id:
        q = q.filter(FuelEntry.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(FuelEntry.driver_id == driver_id)
    if fuel_purpose:
        q = q.filter(FuelEntry.fuel_purpose == FuelPurpose(fuel_purpose).value)

    logs = q.order_by(FuelEntry.id.desc()).all()
    rows = []
    totals_by_purpose: dict[str, float] = {
        FuelPurpose.OFFICIAL.value: 0.0,
        FuelPurpose.PERSONAL.value: 0.0,
        FuelPurpose.SCHOOL_VAN.value: 0.0,
        FuelPurpose.EDUCATION.value: 0.0,
    }

    for l in logs:
        amt = float(l.amount or 0)
        purpose = (l.fuel_purpose or FuelPurpose.OFFICIAL.value)
        totals_by_purpose[purpose] = totals_by_purpose.get(purpose, 0.0) + amt
        rows.append(
            [
                l.id,
                l.slip_no,
                l.vehicle.plate_no if l.vehicle else "",
                l.driver.name if l.driver else "",
                l.trip_id or "",
                l.fuel_date.isoformat() if l.fuel_date else "",
                purpose,
                str(l.liters),
                str(l.rate or ""),
                str(l.amount or ""),
                l.status.value,
            ]
        )

    rows.append([])
    rows.append(["summary", "fuel_purpose", "total_amount"])
    for p in [FuelPurpose.OFFICIAL, FuelPurpose.PERSONAL, FuelPurpose.SCHOOL_VAN, FuelPurpose.EDUCATION]:
        rows.append(["summary", p.value, f"{totals_by_purpose.get(p.value, 0.0):.2f}"])

    return _csv_response(
        "fuel_entries.csv",
        rows,
        ["id", "slip_no", "vehicle", "driver", "trip_id", "fuel_date", "fuel_purpose", "liters", "rate", "amount", "status"],
    )


@bp.get("/fuel.pdf")
@login_required
def fuel_pdf():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = FuelEntry.query
    if start_dt:
        q = q.filter(FuelEntry.created_at >= start_dt)
    if end_dt:
        q = q.filter(FuelEntry.created_at <= end_dt)
    if vehicle_id:
        q = q.filter(FuelEntry.vehicle_id == vehicle_id)
    if driver_id:
        q = q.filter(FuelEntry.driver_id == driver_id)
    if fuel_purpose:
        q = q.filter(FuelEntry.fuel_purpose == FuelPurpose(fuel_purpose).value)

    logs = q.order_by(FuelEntry.id.desc()).all()
    rows = []
    totals_by_purpose: dict[str, float] = {
        FuelPurpose.OFFICIAL.value: 0.0,
        FuelPurpose.PERSONAL.value: 0.0,
        FuelPurpose.SCHOOL_VAN.value: 0.0,
        FuelPurpose.EDUCATION.value: 0.0,
    }

    for l in logs:
        purpose = (l.fuel_purpose or FuelPurpose.OFFICIAL.value)
        totals_by_purpose[purpose] = totals_by_purpose.get(purpose, 0.0) + float(l.amount or 0)
        rows.append(
            [
                l.id,
                l.slip_no,
                l.vehicle.plate_no if l.vehicle else "",
                l.driver.name if l.driver else "",
                l.trip_id or "",
                l.fuel_date.isoformat() if l.fuel_date else "",
                purpose,
                str(l.liters),
                str(l.rate or ""),
                str(l.amount or ""),
                l.status.value,
            ]
        )

    rows.append(["", "", "", "", "", "", "", "", "", "", ""])
    rows.append(["SUMMARY", "", "", "", "", "", "PURPOSE", "", "", "TOTAL", ""])
    for p in [FuelPurpose.OFFICIAL, FuelPurpose.PERSONAL, FuelPurpose.SCHOOL_VAN, FuelPurpose.EDUCATION]:
        rows.append(["", "", "", "", "", "", p.value, "", "", f"{totals_by_purpose.get(p.value, 0.0):.2f}", ""])

    return _pdf_simple_table(
        "fuel_entries.pdf",
        "Fuel Entries Report",
        ["id", "slip_no", "vehicle", "driver", "trip", "fuel_date", "fuel_purpose", "liters", "rate", "amount", "status"],
        rows,
        subtitle=_subtitle(form),
        landscape_mode=True,
    )


@bp.get("/work-orders.csv")
@login_required
def work_orders_csv():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = WorkOrder.query
    if start_dt:
        q = q.filter(WorkOrder.opened_at >= start_dt)
    if end_dt:
        q = q.filter(WorkOrder.opened_at <= end_dt)
    if vehicle_id:
        q = q.filter(WorkOrder.vehicle_id == vehicle_id)

    wos = q.order_by(WorkOrder.id.desc()).all()
    rows = []
    for wo in wos:
        rows.append(
            [
                wo.id,
                wo.status.value,
                wo.vehicle.plate_no if wo.vehicle else "",
                wo.title,
                wo.opened_at.strftime("%Y-%m-%d") if wo.opened_at else "",
            ]
        )
    return _csv_response(
        "work_orders.csv",
        rows,
        ["id", "status", "vehicle", "title", "opened_at"],
    )


@bp.get("/work-orders.pdf")
@login_required
def work_orders_pdf():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = WorkOrder.query
    if start_dt:
        q = q.filter(WorkOrder.opened_at >= start_dt)
    if end_dt:
        q = q.filter(WorkOrder.opened_at <= end_dt)
    if vehicle_id:
        q = q.filter(WorkOrder.vehicle_id == vehicle_id)

    wos = q.order_by(WorkOrder.id.desc()).all()
    rows = []
    for wo in wos:
        rows.append(
            [
                wo.id,
                wo.status.value,
                wo.vehicle.plate_no if wo.vehicle else "",
                wo.title,
            ]
        )
    return _pdf_simple_table(
        "work_orders.pdf",
        "Work Orders Report",
        ["id", "status", "vehicle", "title"],
        rows,
        subtitle=_subtitle(form),
        landscape_mode=True,
    )


@bp.get("/preventive-schedules.csv")
@login_required
def preventive_schedules_csv():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = PreventiveSchedule.query
    if vehicle_id:
        q = q.filter(PreventiveSchedule.vehicle_id == vehicle_id)
    schedules = q.order_by(PreventiveSchedule.id.desc()).all()

    rows = []
    for s in schedules:
        rows.append(
            [
                s.id,
                s.vehicle.plate_no if s.vehicle else "",
                s.title,
                s.interval_km or "",
                s.interval_days or "",
                s.active,
            ]
        )
    return _csv_response(
        "preventive_schedules.csv",
        rows,
        ["id", "vehicle", "title", "interval_km", "interval_days", "active"],
    )


@bp.get("/preventive-schedules.pdf")
@login_required
def preventive_schedules_pdf():
    form, start_dt, end_dt, vehicle_id, driver_id, fuel_purpose = _parse_date_range()
    q = PreventiveSchedule.query
    if vehicle_id:
        q = q.filter(PreventiveSchedule.vehicle_id == vehicle_id)
    schedules = q.order_by(PreventiveSchedule.id.desc()).all()

    rows = []
    for s in schedules:
        rows.append(
            [
                s.id,
                s.vehicle.plate_no if s.vehicle else "",
                s.title,
                s.interval_km or "",
                s.interval_days or "",
            ]
        )
    return _pdf_simple_table(
        "preventive_schedules.pdf",
        "Preventive Schedules Report",
        ["id", "vehicle", "title", "km", "days"],
        rows,
        subtitle=_subtitle(form),
        landscape_mode=True,
    )




