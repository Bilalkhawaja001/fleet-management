import re

from app import create_app
from app.extensions import db
from app.models import Driver, Role, Trip, TripExpense, TripItem, TripStatus, UsageType, User, Vehicle


class TripWorkflowTestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_trip_workflow.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = False


def _extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert m, "csrf token not found"
    return m.group(1)


def _login(client, user_id: int = 1):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def _seed_user_vehicle_driver():
    admin = User(username="trip_admin", role=Role.ADMIN, is_active=True)
    admin.set_password("StrongPass1")
    db.session.add(admin)

    v = Vehicle(plate_no="TRP-001", make_model="Hiace", status="active", category="General")
    d = Driver(name="Driver One", status="active")
    db.session.add(v)
    db.session.add(d)
    db.session.commit()
    return v.id, d.id


def test_trip_create_success():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()

    client = app.test_client()
    _login(client)

    page = client.get("/trips/new")
    token = _extract_csrf(page.get_data(as_text=True))

    res = client.post(
        "/trips/new",
        data={
            "csrf_token": token,
            "usage_type": UsageType.OFFICIAL.value,
            "department": "Operations",
            "employee_name": "Bilal",
            "origin": "Nooriabad",
            "destination_city": "Karachi",
            "destination": "Head Office",
            "time_out": "2026-02-18T10:00",
            "vehicle_id": str(vehicle_id),
            "driver_id": str(driver_id),
            "odometer_start": "1000",
            "notes": "Quick trip",
            "status": TripStatus.PLANNED.value,
        },
        follow_redirects=True,
    )

    assert res.status_code == 200
    with app.app_context():
        trip = Trip.query.order_by(Trip.id.desc()).first()
        assert trip is not None
        assert trip.usage_type == UsageType.OFFICIAL
        assert trip.department == "Operations"


def test_end_plus_success_saves_company_items_and_status_transition():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()
        t = Trip(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            usage_type=UsageType.OFFICIAL,
            department="Ops",
            employee_name="User",
            origin="A",
            destination_city="Karachi",
            destination="B",
            status=TripStatus.IN_TRANSIT,
            odometer_start=1500,
        )
        db.session.add(t)
        db.session.commit()
        trip_id = t.id

    client = app.test_client()
    _login(client)

    page = client.get("/trips/")
    token = _extract_csrf(page.get_data(as_text=True))

    res = client.post(
        f"/trips/{trip_id}/end-plus",
        data={
            "csrf_token": token,
            "end_time": "2026-02-18T12:00",
            "end_odometer": "1650",
            "notes": "Completed",
            "expense_type[]": ["toll"],
            "expense_amount[]": ["120"],
            "expense_remarks[]": ["M9 toll"],
            "item_ownership[]": ["company"],
            "item_gatepass_no[]": ["GP-001"],
            "item_department[]": ["Spinning"],
            "item_description[]": ["Cotton Rolls"],
            "item_qty[]": ["2"],
            "item_uom[]": ["roll"],
            "item_destination[]": ["Warehouse"],
            "item_return_type[]": ["returnable"],
            "item_notes[]": ["Handle carefully"],
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["running_km"] == 150

    with app.app_context():
        t = db.session.get(Trip, trip_id)
        assert t.status == TripStatus.COMPLETED
        assert t.running_km == 150
        assert TripExpense.query.filter(TripExpense.trip_id == trip_id).count() == 1
        assert TripItem.query.filter(TripItem.trip_id == trip_id).count() == 1


def test_end_plus_personal_items_save_with_minimal_fields():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()
        t = Trip(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            usage_type=UsageType.PERSONAL,
            department="Ops",
            employee_name="User",
            origin="A",
            destination_city="Karachi",
            destination="B",
            status=TripStatus.ASSIGNED,
            odometer_start=500,
        )
        db.session.add(t)
        db.session.commit()
        trip_id = t.id

    client = app.test_client()
    _login(client)
    token = _extract_csrf(client.get("/trips/").get_data(as_text=True))

    res = client.post(
        f"/trips/{trip_id}/end-plus",
        data={
            "csrf_token": token,
            "end_time": "2026-02-18T13:00",
            "end_odometer": "550",
            "item_ownership[]": ["personal"],
            "item_gatepass_no[]": [""],
            "item_department[]": [""],
            "item_description[]": ["Laptop Bag"],
            "item_qty[]": ["1"],
            "item_uom[]": ["pcs"],
            "item_destination[]": ["Home"],
            "item_return_type[]": ["not_returnable"],
            "item_notes[]": ["Personal item"],
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert res.status_code == 200
    with app.app_context():
        assert TripItem.query.filter(TripItem.trip_id == trip_id).count() == 1


def test_end_plus_rejects_invalid_odometer():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()
        t = Trip(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            usage_type=UsageType.OFFICIAL,
            department="Ops",
            employee_name="User",
            origin="A",
            destination_city="Karachi",
            destination="B",
            status=TripStatus.IN_TRANSIT,
            odometer_start=2000,
        )
        db.session.add(t)
        db.session.commit()
        trip_id = t.id

    client = app.test_client()
    _login(client)
    token = _extract_csrf(client.get("/trips/").get_data(as_text=True))

    res = client.post(
        f"/trips/{trip_id}/end-plus",
        data={"csrf_token": token, "end_time": "2026-02-18T12:00", "end_odometer": "1900"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


def test_end_plus_csrf_enforced():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()
        t = Trip(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            usage_type=UsageType.OFFICIAL,
            department="Ops",
            employee_name="User",
            origin="A",
            destination_city="Karachi",
            destination="B",
            status=TripStatus.ASSIGNED,
            odometer_start=100,
        )
        db.session.add(t)
        db.session.commit()
        trip_id = t.id

    client = app.test_client()
    _login(client)

    res = client.post(
        f"/trips/{trip_id}/end-plus",
        data={"end_time": "2026-02-18T12:00", "end_odometer": "200"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert res.status_code == 400
