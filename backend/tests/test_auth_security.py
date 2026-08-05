import os

os.environ.setdefault("DATABASE_URL", "postgresql://portfolio:test@localhost:5432/portfolio_db")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-key-must-be-32-chars!")
os.environ.setdefault("MEDIA_DIR", "/tmp/test-media")

import psycopg2  # noqa: E402
import pytest  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

TEST_USERNAME = "auth_sec_test_admin"
TEST_EMAIL = "auth_sec_test_admin@example.com"
TEST_PASSWORD = "test-password-123"


def _create_test_user():
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (TEST_USERNAME,))
            if cur.fetchone():
                return
            cur.execute(
                "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)",
                (TEST_USERNAME, TEST_EMAIL, hash_password(TEST_PASSWORD)),
            )
    finally:
        conn.close()


def _delete_test_user():
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE username = %s", (TEST_USERNAME,))
    finally:
        conn.close()


def _reset_test_user_password():
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET hashed_password = %s WHERE username = %s",
                (hash_password(TEST_PASSWORD), TEST_USERNAME),
            )
    finally:
        conn.close()


@pytest.fixture
def auth_client():
    _create_test_user()
    client = TestClient(app)
    res = client.post("/api/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    assert res.status_code == 200
    yield client
    _reset_test_user_password()
    _delete_test_user()


def test_login_cookie_is_httponly_and_samesite_lax(auth_client):
    set_cookie = auth_client.cookies.get("access_token")
    assert set_cookie is not None


def test_login_cookie_flags_present():
    client = TestClient(app)
    _create_test_user()
    try:
        res = client.post("/api/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD})
        assert res.status_code == 200
        raw_header = res.headers.get("set-cookie", "")
        assert "HttpOnly" in raw_header
        assert "samesite=lax" in raw_header.lower()
    finally:
        _delete_test_user()


def test_login_cookie_is_secure_when_cookie_secure_enabled(monkeypatch):
    monkeypatch.setattr(settings, "cookie_secure", True)
    client = TestClient(app)
    _create_test_user()
    try:
        res = client.post("/api/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD})
        assert res.status_code == 200
        raw_header = res.headers.get("set-cookie", "")
        assert "secure" in raw_header.lower()
    finally:
        _delete_test_user()


def test_unauthenticated_request_rejected():
    client = TestClient(app)
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_password_change_invalidates_old_token(auth_client):
    old_cookie_value = auth_client.cookies.get("access_token")
    assert old_cookie_value is not None

    res = auth_client.put(
        "/api/auth/me",
        json={"current_password": TEST_PASSWORD, "new_password": "a-new-strong-password-456"},
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
