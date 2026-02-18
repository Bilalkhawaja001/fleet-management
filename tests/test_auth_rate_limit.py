from app import create_app


def test_login_rate_limit_triggers_429():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    last_status = None
    for _ in range(6):
        resp = client.post("/auth/login", data={"username": "x", "password": "y"})
        last_status = resp.status_code

    assert last_status == 429
