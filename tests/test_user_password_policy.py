import pytest

from app.models.user import User


def test_password_policy_rejects_weak_passwords():
    u = User(username="tester")

    with pytest.raises(ValueError):
        u.set_password("short")

    with pytest.raises(ValueError):
        u.set_password("alllowercase1")

    with pytest.raises(ValueError):
        u.set_password("ALLUPPERCASE1")

    with pytest.raises(ValueError):
        u.set_password("NoDigitsHere")


def test_password_policy_accepts_strong_password():
    u = User(username="tester2")
    u.set_password("StrongPass1")
    assert u.password_hash
    assert u.check_password("StrongPass1") is True
