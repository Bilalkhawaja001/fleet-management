import re

from app import create_app
from app.extensions import db
from app.models import Driver, Role, User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_delete_csrf.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False


def _extract_csrf(html: str, form_id: str) -> str:
    pattern = rf'<form[^>]*id="{re.escape(form_id)}"[\s\S]*?name="csrf_token" value="([^"]+)"'
    m = re.search(pattern, html)
    assert m, f"csrf token not found for form {form_id}"
    return m.group(1)


def test_delete_routes_do_not_allow_get():
    app = create_app(TestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(username="admin_get", role=Role.ADMIN, is_active=True)
        admin.set_password("StrongPass1")
        db.session.add(admin)

        d = Driver(name="Delete Me", status="active")
        db.session.add(d)
        db.session.commit()
        driver_id = d.id

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
        sess["_fresh"] = True

    assert client.get(f"/drivers/{driver_id}/delete").status_code in (404, 405)
    assert client.get("/fleet/vehicles/1/delete").status_code in (404, 405)
    assert client.get("/trips/1/delete").status_code in (404, 405)


def test_driver_delete_with_csrf_token_succeeds():
    app = create_app(TestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(username="admin_post", role=Role.ADMIN, is_active=True)
        admin.set_password("StrongPass1")
        db.session.add(admin)

        d = Driver(name="Delete Driver", status="active")
        db.session.add(d)
        db.session.commit()
        driver_id = d.id

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
        sess["_fresh"] = True

    page = client.get("/drivers/")
    assert page.status_code == 200
    token = _extract_csrf(page.get_data(as_text=True), f"drv-del-{driver_id}")

    res = client.post(f"/drivers/{driver_id}/delete", data={"csrf_token": token}, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        assert db.session.get(Driver, driver_id) is None
