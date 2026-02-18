from app import create_app
from app.extensions import db
from app.models import Role, User


class FuelPageTestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_fuel_page.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = False


def test_fuel_page_renders_200():
    app = create_app(FuelPageTestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username="fuel_admin_page", role=Role.ADMIN, is_active=True)
        admin.set_password("StrongPass1")
        db.session.add(admin)
        db.session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
        sess["_fresh"] = True

    res = client.get("/fuel/")
    assert res.status_code == 200
    assert "Fuel Logs" in res.get_data(as_text=True)
