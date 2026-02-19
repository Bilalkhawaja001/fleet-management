import io
from datetime import datetime

from app import create_app
from app.extensions import db
from app.models import DocumentAttachment, Role, Trip, TripStatus, User, Vehicle


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


def test_trips_csv_with_string_usage_type_and_zero_ids_and_empty_filters():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, vehicle_id = _seed()
        db.session.add(
            Trip(
                vehicle_id=vehicle_id,
                usage_type="official",  # string path (not enum object)
                status=TripStatus.PLANNED,
                origin="Nooriabad",
                destination_city="Karachi",
                destination="HQ",
                time_out=datetime(2026, 2, 19, 10, 0),
            )
        )
        db.session.commit()

    client = app.test_client(); _login(client, user_id)
    res = client.get('/reports/trips.csv?start_date=&end_date=&vehicle_id=0&driver_id=0&fuel_purpose=')
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "usage_type" in body
    assert "official" in body


def test_documents_get_loads():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, _ = _seed()

    client = app.test_client(); _login(client, user_id)
    res = client.get('/documents/')
    assert res.status_code == 200


def test_documents_upload_download_delete_flow():
    app = create_app(CriticalEndpointsConfig)
    with app.app_context():
        db.drop_all(); db.create_all()
        user_id, vehicle_id = _seed()

    client = app.test_client(); _login(client, user_id)

    pdf_file = (io.BytesIO(b'%PDF-1.4\n%test\n'), 'sample.pdf')
    upload_res = client.post('/documents/new', data={
        'vehicle_id': str(vehicle_id),
        'trip_id': '0',
        'doc_type': 'insurance',
        'doc_name': 'With PDF',
        'doc_number': 'DOC-200',
        'issue_date': '2026-02-19',
        'expiry_date': '2026-12-31',
        'attachments': pdf_file,
    }, content_type='multipart/form-data')
    assert upload_res.status_code == 302

    with app.app_context():
        a = DocumentAttachment.query.order_by(DocumentAttachment.id.desc()).first()
        assert a is not None
        aid = a.id

    dl_res = client.get(f'/documents/{aid}/download')
    assert dl_res.status_code == 200

    del_res = client.post(f'/documents/{aid}/delete', data={'csrf_token': 'x'})
    assert del_res.status_code == 302

    with app.app_context():
        assert db.session.get(DocumentAttachment, aid) is None


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
