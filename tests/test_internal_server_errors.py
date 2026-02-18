from app import create_app
from app.extensions import db
from app.models import Driver, Role, Trip, TripStatus, UsageType, User, Vehicle


class SmokeConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_smoke_routes.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = False


def _login(client, user_id: int = 1):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def _seed_minimal_data():
    admin = User(username="smoke_admin", role=Role.ADMIN, is_active=True)
    admin.set_password("StrongPass1")
    db.session.add(admin)
    v = Vehicle(plate_no="SMK-1", make_model="Truck", status="active", category="General")
    d = Driver(name="Smoke Driver", status="active")
    db.session.add_all([v, d])
    db.session.flush()
    t = Trip(
        vehicle_id=v.id,
        driver_id=d.id,
        usage_type=UsageType.OFFICIAL,
        department="Centralized",
        employee_name="Smoke",
        origin="Nooriabad",
        destination_city="Karachi",
        destination="HQ",
        status=TripStatus.PLANNED,
        odometer_start=100,
    )
    db.session.add(t)
    db.session.commit()
    return t.id


def test_core_pages_no_internal_server_error():
    app = create_app(SmokeConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        trip_id = _seed_minimal_data()

    client = app.test_client()
    _login(client)

    urls = [
        "/dashboard/",
        "/fleet/vehicles",
        "/drivers/",
        "/trips/",
        "/trips/new",
        f"/trips/{trip_id}/edit",
        "/bookings/",
        "/fuel/",
        "/documents/",
        "/incidents/",
        "/maintenance/schedules",
        "/maintenance/work-orders",
        "/reports/",
        "/users/",
    ]

    for url in urls:
        r = client.get(url)
        assert r.status_code < 500, f"{url} returned {r.status_code}"
