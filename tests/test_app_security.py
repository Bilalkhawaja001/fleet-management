from app import create_app


def test_app_boot_and_security_defaults():
    app = create_app()

    assert app is not None
    assert app.config["WTF_CSRF_ENABLED"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["REMEMBER_COOKIE_HTTPONLY"] is True


def test_security_headers_present_on_health():
    app = create_app()
    client = app.test_client()

    res = client.get("/auth/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "Content-Security-Policy" in res.headers
