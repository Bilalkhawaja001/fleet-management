import re

from app import create_app
from app.extensions import db
from app.models import Driver, ItemOwnership, Role, Trip, TripExpense, TripItem, TripStatus, UsageType, User, Vehicle


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


def test_trip_create_saves_company_items():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()

    client = app.test_client(); _login(client)
    token = _extract_csrf(client.get('/trips/new').get_data(as_text=True))

    res = client.post('/trips/new', data={
        'csrf_token': token,
        'usage_type': UsageType.OFFICIAL.value,
        'department': 'Operations',
        'employee_name': 'Bilal',
        'origin': 'Nooriabad',
        'destination_city': 'Karachi',
        'destination': 'Head Office',
        'time_out': '2026-02-18T10:00',
        'vehicle_id': str(vehicle_id),
        'driver_id': str(driver_id),
        'odometer_start': '1000',
        'status': TripStatus.PLANNED.value,
        'item_ownership[]': ['company'],
        'item_gatepass_no[]': ['GP-100'],
        'item_department[]': ['Spinning'],
        'item_description[]': ['Cotton Bale'],
        'item_qty[]': ['2'],
        'item_uom[]': ['bag'],
        'item_destination[]': ['Warehouse'],
        'item_return_type[]': ['returnable'],
        'item_notes[]': ['fragile'],
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        t = Trip.query.order_by(Trip.id.desc()).first()
        assert t is not None
        assert TripItem.query.filter(TripItem.trip_id == t.id).count() == 1
        it = TripItem.query.filter(TripItem.trip_id == t.id).first()
        assert it.ownership == ItemOwnership.COMPANY
        assert it.gatepass_no == 'GP-100'


def test_trip_create_saves_personal_items_minimal():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()

    client = app.test_client(); _login(client)
    token = _extract_csrf(client.get('/trips/new').get_data(as_text=True))

    res = client.post('/trips/new', data={
        'csrf_token': token,
        'usage_type': UsageType.PERSONAL.value,
        'department': 'Operations',
        'employee_name': 'Bilal',
        'origin': 'Nooriabad',
        'destination_city': 'Karachi',
        'destination': 'Home',
        'time_out': '2026-02-18T10:00',
        'vehicle_id': str(vehicle_id),
        'driver_id': str(driver_id),
        'odometer_start': '1000',
        'status': TripStatus.PLANNED.value,
        'item_ownership[]': ['personal'],
        'item_gatepass_no[]': [''],
        'item_department[]': [''],
        'item_description[]': ['Laptop'],
        'item_qty[]': ['1'],
        'item_uom[]': ['pcs'],
        'item_destination[]': ['Home'],
        'item_return_type[]': ['not_returnable'],
        'item_notes[]': [''],
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        t = Trip.query.order_by(Trip.id.desc()).first()
        assert TripItem.query.filter(TripItem.trip_id == t.id).count() == 1


def test_end_plus_requires_return_confirmation_for_returnables():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()
        t = Trip(vehicle_id=vehicle_id, driver_id=driver_id, usage_type=UsageType.OFFICIAL, department='Ops', employee_name='U', origin='A', destination_city='Karachi', destination='B', status=TripStatus.IN_TRANSIT, odometer_start=100)
        db.session.add(t); db.session.flush()
        db.session.add(TripItem(trip_id=t.id, ownership='company', gatepass_no='GP-1', department='Ops', item_description='Material', qty=1, uom='pcs', destination='Gate', return_type='returnable'))
        db.session.commit(); trip_id=t.id

    client = app.test_client(); _login(client)
    token = _extract_csrf(client.get('/trips/').get_data(as_text=True))
    res = client.post(f'/trips/{trip_id}/end-plus', data={'csrf_token': token, 'end_time': '2026-02-18T12:00', 'end_odometer': '120'}, headers={'X-Requested-With':'XMLHttpRequest'})
    assert res.status_code == 400


def test_end_plus_success_and_odometer_validation_and_csrf():
    app = create_app(TripWorkflowTestConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        vehicle_id, driver_id = _seed_user_vehicle_driver()
        t = Trip(vehicle_id=vehicle_id, driver_id=driver_id, usage_type=UsageType.OFFICIAL, department='Ops', employee_name='U', origin='A', destination_city='Karachi', destination='B', status=TripStatus.ASSIGNED, odometer_start=500)
        db.session.add(t); db.session.commit(); trip_id=t.id

    client = app.test_client(); _login(client)
    token = _extract_csrf(client.get('/trips/').get_data(as_text=True))

    bad = client.post(f'/trips/{trip_id}/end-plus', data={'csrf_token': token, 'end_time': '2026-02-18T12:00', 'end_odometer': '400'}, headers={'X-Requested-With':'XMLHttpRequest'})
    assert bad.status_code == 400

    ok = client.post(f'/trips/{trip_id}/end-plus', data={
        'csrf_token': token,
        'end_time': '2026-02-18T12:00',
        'end_odometer': '550',
        'expense_type[]': ['toll'],
        'expense_amount[]': ['100'],
        'expense_remarks[]': ['toll gate'],
    }, headers={'X-Requested-With':'XMLHttpRequest'})
    assert ok.status_code == 200

    with app.app_context():
        t = db.session.get(Trip, trip_id)
        assert t.status == TripStatus.COMPLETED
        assert t.running_km == 50
        assert TripExpense.query.filter(TripExpense.trip_id == trip_id).count() == 1

    csrf_fail = client.post(f'/trips/{trip_id}/end-plus', data={'end_time': '2026-02-18T12:00', 'end_odometer': '560'}, headers={'X-Requested-With':'XMLHttpRequest'})
    assert csrf_fail.status_code == 400
