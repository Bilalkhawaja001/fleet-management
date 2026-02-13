import csv
import io
from datetime import datetime, date, time

from flask import Blueprint, render_template, Response, send_file, request
from flask_login import login_required

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from ...models import Trip, FuelLog, WorkOrder
from .forms import DateRangeForm

bp = Blueprint("reports", __name__, url_prefix="/reports")


def _parse_date_range():
    form = DateRangeForm(request.args)

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
    return form, start_dt, end_dt


@bp.get("/")
@login_required
def index():
    form, _, _ = _parse_date_range()
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


def _pdf_simple_table(filename: str, title: str, header, rows):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title)

    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

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


@bp.get("/trips.csv")
@login_required
def trips_csv():
    form, start_dt, end_dt = _parse_date_range()
    q = Trip.query
    # Trips have created_at
    if start_dt:
        q = q.filter(Trip.created_at >= start_dt)
    if end_dt:
        q = q.filter(Trip.created_at <= end_dt)
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
    form, start_dt, end_dt = _parse_date_range()
    q = Trip.query
    if start_dt:
        q = q.filter(Trip.created_at >= start_dt)
    if end_dt:
        q = q.filter(Trip.created_at <= end_dt)
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
    )


@bp.get("/fuel.csv")
@login_required
def fuel_csv():
    form, start_dt, end_dt = _parse_date_range()
    q = FuelLog.query
    # FuelLog has filled_at
    if start_dt:
        q = q.filter(FuelLog.filled_at >= start_dt)
    if end_dt:
        q = q.filter(FuelLog.filled_at <= end_dt)
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
    form, start_dt, end_dt = _parse_date_range()
    q = FuelLog.query
    if start_dt:
        q = q.filter(FuelLog.filled_at >= start_dt)
    if end_dt:
        q = q.filter(FuelLog.filled_at <= end_dt)
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
    )


@bp.get("/work-orders.csv")
@login_required
def work_orders_csv():
    form, start_dt, end_dt = _parse_date_range()
    q = WorkOrder.query
    # WorkOrder has opened_at
    if start_dt:
        q = q.filter(WorkOrder.opened_at >= start_dt)
    if end_dt:
        q = q.filter(WorkOrder.opened_at <= end_dt)
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
    form, start_dt, end_dt = _parse_date_range()
    q = WorkOrder.query
    if start_dt:
        q = q.filter(WorkOrder.opened_at >= start_dt)
    if end_dt:
        q = q.filter(WorkOrder.opened_at <= end_dt)
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
    )
