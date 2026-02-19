import io

from app import create_app
from app.extensions import db
from app.models import Role, User, Vehicle


class CriticalEndpointsConfig:
    TESTING = True
    SECRET_KEY = "test-critical"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_critical_endpoints.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def _seed():
    admin = User(username="critical_admin", role=Role.ADMIN, is_active=True)
    admin.set_password("StrongPass1")
    db.session.add(admin)
    v = Vehicle(plate_no="CRT-001", make_model="Hiace", status="active", category="General")
    db.session.add(v)
    db.session.commit()
    return admin.id, v.id


def test_dashboard_get_loads():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, _ = _seed()

    client = app.test_client(); _login(client, user_id)
    res = client.get('/dashboard/')
    assert res.status_code == 200


def test_reports_get_loads():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, _ = _seed()

    client = app.test_client(); _login(client, user_id)
    res = client.get('/reports/')
    assert res.status_code == 200


def test_documents_get_loads():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, _ = _seed()

    client = app.test_client(); _login(client, user_id)
    res = client.get('/documents/')
    assert res.status_code == 200


def test_documents_post_no_file_and_reports_post_with_querystring():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, vehicle_id = _seed()

    client = app.test_client(); _login(client, user_id)

    doc_res = client.post('/documents/new', data={
        'vehicle_id': str(vehicle_id),
        'trip_id': '0',
        'doc_type': 'insurance',
        'doc_name': 'No File Doc',
        'doc_number': 'DOC-100',
        'issue_date': '2026-02-19',
        'expiry_date': '2026-12-31',
    }, content_type='multipart/form-data')
    assert doc_res.status_code == 302

    csv_file = (io.BytesIO(b'c1,c2\n1,2\n'), 'sample.csv')
    rpt_res = client.post('/reports/?start_date=2026-02-01&end_date=2026-02-19&vehicle_id=0&driver_id=0&fuel_purpose=official', data={
        'report_file': csv_file,
    }, content_type='multipart/form-data')
    assert rpt_res.status_code == 200
