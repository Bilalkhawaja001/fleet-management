from datetime import date, datetime, time, timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from ...extensions import db
from ...models import (
    Driver,
    FuelEntry,
    FuelEntryStatus,
    Incident,
    IncidentStatus,
    Trip,
    TripStatus,
    Vehicle,
    VehicleBooking,
    BookingStatus,
    VehicleDocument,
    VehicleDocStatus,
    VehicleDocType,
    WorkOrder,
    WorkOrderStatus,
)

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("/")
@login_required
def index():
    today = date.today()
    start_dt = datetime.combine(today, time.min)
    end_dt = datetime.combine(today, time.max)

    # Trips today (based on time_out)
    trips_today_q = Trip.query.filter(Trip.time_out >= start_dt, Trip.time_out <= end_dt)
    trips_today_total = trips_today_q.count()

    trips_today_by_status = {
        s.value: trips_today_q.filter(Trip.status == s).count() for s in TripStatus
    }

    # Fleet counts
    vehicles_total = Vehicle.query.count()
    drivers_total = Driver.query.count()

    # Vehicles inside/outside mill (heuristic): outside = vehicles currently in an IN_TRANSIT trip
    vehicles_outside = (
        db.session.query(Trip.vehicle_id)
        .filter(Trip.vehicle_id.isnot(None), Trip.status == TripStatus.IN_TRANSIT)
        .distinct()
        .count()
    )
    vehicles_inside = max(0, vehicles_total - vehicles_outside)

    # Maintenance
    open_wos_q = WorkOrder.query.filter(WorkOrder.status.in_([WorkOrderStatus.OPEN, WorkOrderStatus.IN_PROGRESS]))
    open_work_orders = open_wos_q.count()
    vehicles_under_maintenance = (
        db.session.query(WorkOrder.vehicle_id)
        .filter(WorkOrder.status.in_([WorkOrderStatus.OPEN, WorkOrderStatus.IN_PROGRESS]))
        .distinct()
        .count()
    )

    # Fuel verification
    fuel_pending = FuelEntry.query.filter(FuelEntry.status == FuelEntryStatus.PENDING).count()

    # Documents expiring/expired + missing
    exp_window_end = today + timedelta(days=30)
    docs_expiring = VehicleDocument.query.filter(
        VehicleDocument.status == VehicleDocStatus.ACTIVE,
        VehicleDocument.expiry_date >= today,
        VehicleDocument.expiry_date <= exp_window_end,
    ).count()
    docs_expired = VehicleDocument.query.filter(
        VehicleDocument.status == VehicleDocStatus.ACTIVE,
        VehicleDocument.expiry_date < today,
    ).count()

    # Missing docs: count vehicles that are missing at least one mandatory doc type
    mandatory_types = [t for t in VehicleDocType]
    vehicles = Vehicle.query.all()
    missing_docs_vehicles = 0
    for v in vehicles:
        active_types = {
            d.doc_type
            for d in (v.documents or [])
            if d.status == VehicleDocStatus.ACTIVE
        }
        missing = any(t not in active_types for t in mandatory_types)
        if missing:
            missing_docs_vehicles += 1

    # Incidents
    incidents_open = Incident.query.filter(Incident.status != IncidentStatus.CLOSED).count()

    # Recent tables (limited)
    recent_trips = (
        trips_today_q.order_by(Trip.time_out.desc().nullslast(), Trip.id.desc()).limit(10).all()
    )

    # Upcoming scheduled trips (next 7 days) based on time_out
    upcoming_start = datetime.combine(today + timedelta(days=1), time.min)
    upcoming_end = datetime.combine(today + timedelta(days=7), time.max)
    upcoming_trips = (
        Trip.query.filter(
            Trip.time_out >= upcoming_start,
            Trip.time_out <= upcoming_end,
            Trip.status.in_([TripStatus.PLANNED, TripStatus.ASSIGNED]),
        )
        .order_by(Trip.time_out.asc())
        .limit(10)
        .all()
    )

    # Upcoming vehicle bookings (next 7 days)
    upcoming_bookings = (
        VehicleBooking.query.filter(
            VehicleBooking.start_at >= upcoming_start,
            VehicleBooking.start_at <= upcoming_end,
            VehicleBooking.status == BookingStatus.SCHEDULED,
        )
        .order_by(VehicleBooking.start_at.asc())
        .limit(10)
        .all()
    )
    recent_work_orders = open_wos_q.order_by(WorkOrder.id.desc()).limit(10).all()
    recent_docs_expiring = (
        VehicleDocument.query.filter(
            VehicleDocument.status == VehicleDocStatus.ACTIVE,
            VehicleDocument.expiry_date <= exp_window_end,
        )
        .order_by(VehicleDocument.expiry_date.asc())
        .limit(10)
        .all()
    )
    recent_fuel_pending = (
        FuelEntry.query.filter(FuelEntry.status == FuelEntryStatus.PENDING)
        .order_by(FuelEntry.id.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        title="Dashboard",
        today=today,
        trips_today_total=trips_today_total,
        trips_today_by_status=trips_today_by_status,
        vehicles_total=vehicles_total,
        drivers_total=drivers_total,
        open_work_orders=open_work_orders,
        vehicles_under_maintenance=vehicles_under_maintenance,
        vehicles_inside=vehicles_inside,
        vehicles_outside=vehicles_outside,
        fuel_pending=fuel_pending,
        docs_expiring=docs_expiring,
        docs_expired=docs_expired,
        missing_docs_vehicles=missing_docs_vehicles,
        incidents_open=incidents_open,
        recent_trips=recent_trips,
        upcoming_trips=upcoming_trips,
        upcoming_bookings=upcoming_bookings,
        upcoming_start=upcoming_start,
        upcoming_end=upcoming_end,
        recent_work_orders=recent_work_orders,
        recent_docs_expiring=recent_docs_expiring,
        recent_fuel_pending=recent_fuel_pending,
    )
