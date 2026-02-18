from app import create_app
from app.extensions import db


class RateLimitTestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_ratelimit.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"


def test_login_rate_limit_triggers_429():
    app = create_app(RateLimitTestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()

    client = app.test_client()

    last_status = None
    for _ in range(6):
        resp = client.post("/auth/login", data={"username": "x", "password": "y"})
        last_status = resp.status_code

    assert last_status == 429
