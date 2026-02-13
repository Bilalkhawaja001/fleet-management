import csv
import io
from datetime import datetime, date, time

from flask import Blueprint, render_template, Response, send_file, request
from flask_login import login_required

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from ...models import Trip, FuelLog, WorkOrder, Vehicle, Driver, PreventiveSchedule
from .forms import DateRangeForm

bp = Blueprint("reports", __name__, url_prefix="/reports")


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

    return form, start_dt, end_dt, vehicle_id, driver_id


@bp.get("/")
@login_required
def index():
    form, _, _, _, _ = _parse_date_range()
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


def _pdf_simple_table(filename: str, title: str, header, rows, subtitle: str | None = None):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4

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
    return f"Range: {s}..{e}{v}{d}".strip()


@bp.get("/trips.csv")
@login_required
def trips_csv():
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
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
        rows.append(
            [
                t.id,
                t.status.value,
                t.vehicle.plate_no if t.vehicle else "",
                t.driver.name if t.driver else "",
                t.origin or "",
                t.destination or "",
            ]
        )
    return _csv_response(
        "trips.csv",
        rows,
        ["id", "status", "vehicle", "driver", "origin", "destination"],
    )


@bp.get("/trips.pdf")
@login_required
def trips_pdf():
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
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
        rows.append(
            [
                t.id,
                t.status.value,
                t.vehicle.plate_no if t.vehicle else "",
                t.driver.name if t.driver else "",
                (t.origin or "") + "->" + (t.destination or ""),
            ]
        )
    return _pdf_simple_table(
        "trips.pdf",
        "Trips Report",
        ["id", "status", "vehicle", "driver", "route"],
        rows,
        subtitle=_subtitle(form),
    )


@bp.get("/fuel.csv")
@login_required
def fuel_csv():
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
    q = FuelLog.query
    if start_dt:
        q = q.filter(FuelLog.filled_at >= start_dt)
    if end_dt:
        q = q.filter(FuelLog.filled_at <= end_dt)
    if vehicle_id:
        q = q.filter(FuelLog.vehicle_id == vehicle_id)

    logs = q.order_by(FuelLog.id.desc()).all()
    rows = []
    for l in logs:
        rows.append(
            [
                l.id,
                l.vehicle.plate_no,
                str(l.liters),
                str(l.amount or ""),
                l.odometer_km or "",
                l.vendor or "",
            ]
        )
    return _csv_response(
        "fuel_logs.csv",
        rows,
        ["id", "vehicle", "liters", "amount", "odometer_km", "vendor"],
    )


@bp.get("/fuel.pdf")
@login_required
def fuel_pdf():
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
    q = FuelLog.query
    if start_dt:
        q = q.filter(FuelLog.filled_at >= start_dt)
    if end_dt:
        q = q.filter(FuelLog.filled_at <= end_dt)
    if vehicle_id:
        q = q.filter(FuelLog.vehicle_id == vehicle_id)

    logs = q.order_by(FuelLog.id.desc()).all()
    rows = []
    for l in logs:
        rows.append(
            [
                l.id,
                l.vehicle.plate_no,
                str(l.liters),
                str(l.amount or ""),
                l.odometer_km or "",
            ]
        )
    return _pdf_simple_table(
        "fuel_logs.pdf",
        "Fuel Logs Report",
        ["id", "vehicle", "liters", "amount", "odometer"],
        rows,
        subtitle=_subtitle(form),
    )


@bp.get("/work-orders.csv")
@login_required
def work_orders_csv():
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
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
                wo.vehicle.plate_no,
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
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
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
                wo.vehicle.plate_no,
                wo.title,
            ]
        )
    return _pdf_simple_table(
        "work_orders.pdf",
        "Work Orders Report",
        ["id", "status", "vehicle", "title"],
        rows,
        subtitle=_subtitle(form),
    )


@bp.get("/preventive-schedules.csv")
@login_required
def preventive_schedules_csv():
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
    q = PreventiveSchedule.query
    if vehicle_id:
        q = q.filter(PreventiveSchedule.vehicle_id == vehicle_id)
    schedules = q.order_by(PreventiveSchedule.id.desc()).all()

    rows = []
    for s in schedules:
        rows.append(
            [
                s.id,
                s.vehicle.plate_no,
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
    form, start_dt, end_dt, vehicle_id, driver_id = _parse_date_range()
    q = PreventiveSchedule.query
    if vehicle_id:
        q = q.filter(PreventiveSchedule.vehicle_id == vehicle_id)
    schedules = q.order_by(PreventiveSchedule.id.desc()).all()

    rows = []
    for s in schedules:
        rows.append(
            [
                s.id,
                s.vehicle.plate_no,
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
    )
