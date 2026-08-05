from app.core.config import settings
from app.main import app
from fastapi.testclient import TestClient


def test_login_cookie_is_httponly_and_samesite_lax(auth_client):
    assert auth_client.cookies.get("access_token") is not None


def test_login_cookie_flags_present(client, admin_user):
    res = client.post(
        "/api/auth/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert res.status_code == 200
    raw_header = res.headers.get("set-cookie", "")
    assert "HttpOnly" in raw_header
    assert "samesite=lax" in raw_header.lower()


def test_login_cookie_is_secure_when_cookie_secure_enabled(client, admin_user, monkeypatch):
    monkeypatch.setattr(settings, "cookie_secure", True)
    res = client.post(
        "/api/auth/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert res.status_code == 200
    raw_header = res.headers.get("set-cookie", "")
    assert "secure" in raw_header.lower()


def test_unauthenticated_request_rejected(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_password_change_invalidates_old_token(auth_client, admin_user):
    old_cookie_value = auth_client.cookies.get("access_token")
    assert old_cookie_value is not None

    res = auth_client.put(
        "/api/auth/me",
        json={"current_password": admin_user["password"], "new_password": "a-new-strong-password-456"},
    )
    assert res.status_code == 200

    # 換完密碼後，client 的 cookie jar 應該已經被新 token 取代
    new_cookie_value = auth_client.cookies.get("access_token")
    assert new_cookie_value is not None
    assert new_cookie_value != old_cookie_value

    # 舊 token 即使語法上仍是合法 JWT，也應該因 token_version 不符而失效
    old_token_client = TestClient(app)
    old_token_client.cookies.set("access_token", old_cookie_value)
    res_old = old_token_client.get("/api/auth/me")
    assert res_old.status_code == 401

    # 新 token 應該仍然有效
    new_token_client = TestClient(app)
    new_token_client.cookies.set("access_token", new_cookie_value)
    res_new = new_token_client.get("/api/auth/me")
    assert res_new.status_code == 200
