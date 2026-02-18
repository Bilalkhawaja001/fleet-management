from datetime import date

from app import create_app
from app.extensions import db
from app.models import Driver, FuelEntry, FuelEntryStatus, FuelPurpose, Role, User, Vehicle


class FuelPurposeTestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_fuel_purpose.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


def _login(client, user_id: int = 1):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def _seed_data():
    admin = User(username="fuel_admin", role=Role.ADMIN, is_active=True)
    admin.set_password("StrongPass1")
    db.session.add(admin)

    vehicle = Vehicle(plate_no="ABC-123", make_model="Corolla", status="active", category="General")
    driver = Driver(name="Ali", status="active")
    db.session.add(vehicle)
    db.session.add(driver)
    db.session.flush()

    entries = [
        FuelEntry(
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            slip_no="SLIP-001",
            fuel_date=date(2026, 2, 18),
            liters=10,
            rate=20,
            amount=200,
            fuel_purpose=FuelPurpose.OFFICIAL,
            status=FuelEntryStatus.PENDING,
        ),
        FuelEntry(
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            slip_no="SLIP-002",
            fuel_date=date(2026, 2, 18),
            liters=5,
            rate=20,
            amount=100,
            fuel_purpose=FuelPurpose.SCHOOL_VAN,
            status=FuelEntryStatus.PENDING,
        ),
        FuelEntry(
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            slip_no="SLIP-003",
            fuel_date=date(2026, 2, 18),
            liters=2,
            rate=20,
            amount=40,
            fuel_purpose=FuelPurpose.EDUCATION,
            status=FuelEntryStatus.PENDING,
        ),
    ]
    db.session.add_all(entries)
    db.session.commit()


def test_fuel_list_filters_by_fuel_purpose():
    app = create_app(FuelPurposeTestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()
        _seed_data()

    client = app.test_client()
    _login(client)

    res = client.get("/fuel/?fuel_purpose=school_van")
    text = res.get_data(as_text=True)

    assert res.status_code == 200
    assert "SLIP-002" in text
    assert "SLIP-001" not in text
    assert "SLIP-003" not in text


def test_fuel_csv_includes_purpose_and_summary_totals():
    app = create_app(FuelPurposeTestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()
        _seed_data()

    client = app.test_client()
    _login(client)

    res = client.get("/reports/fuel.csv")
    csv_text = res.get_data(as_text=True)

    assert res.status_code == 200
    assert "fuel_purpose" in csv_text
    assert "SLIP-001" in csv_text and "official" in csv_text
    assert "SLIP-002" in csv_text and "school_van" in csv_text
    assert "SLIP-003" in csv_text and "education" in csv_text

    assert "summary,official,200.00" in csv_text
    assert "summary,school_van,100.00" in csv_text
    assert "summary,education,40.00" in csv_text
