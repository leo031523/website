import json
import logging

from app.core.security import hash_password


def test_liveness_check_does_not_touch_database(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_readiness_check_succeeds_when_database_available(client):
    res = client.get("/api/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


def test_readiness_check_fails_when_database_unavailable(client, monkeypatch):
    class _BrokenEngine:
        def connect(self):
            raise ConnectionError("simulated database outage")

    monkeypatch.setattr("app.core.database.engine", _BrokenEngine())
    res = client.get("/api/health/ready")
    assert res.status_code == 503
    assert res.json()["database"] == "unavailable"


def test_response_includes_request_id_header(client):
    res = client.get("/api/health")
    assert "x-request-id" in {k.lower() for k in res.headers.keys()}


def test_duplicate_username_via_account_update_returns_409(db_conn, client):
    """update_me 目前沒有事先檢查 username/email 是否重複，
    這裡直接驗證：即使真的撞到資料庫 unique constraint，
    也會被全域的 IntegrityError handler 轉成 409，而不是 500。"""
    import uuid

    user_a = f"test_{uuid.uuid4().hex[:12]}"
    user_b = f"test_{uuid.uuid4().hex[:12]}"
    password = "test-password-123"

    with db_conn, db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s) RETURNING id",
            (user_a, f"{user_a}@example.com", hash_password(password)),
        )
        user_a_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s) RETURNING id",
            (user_b, f"{user_b}@example.com", hash_password(password)),
        )
        user_b_id = cur.fetchone()[0]

    try:
        res = client.post("/api/auth/login", json={"username": user_a, "password": password})
        assert res.status_code == 200

        res = client.put(
            "/api/auth/me",
            json={"username": user_b, "current_password": password},
        )
        assert res.status_code == 409
        assert "request_id" in res.json()
    finally:
        with db_conn, db_conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id IN (%s, %s)", (user_a_id, user_b_id))


def test_revalidate_failure_is_logged_with_slug_and_reason(auth_client, cleanup, caplog, monkeypatch):
    """把 frontend_url 指到一個保證連不上的位址，強制製造 revalidation
    失敗（不依賴當下環境是否真的有 frontend 容器在跑）。revalidation
    失敗不應擋文章建立，但要能從 log 找到是哪篇文章（slug）、
    什麼原因失敗。"""
    from app.core.config import settings

    monkeypatch.setattr(settings, "frontend_url", "http://127.0.0.1:1")

    with caplog.at_level(logging.WARNING, logger="app.revalidate"):
        res = auth_client.post(
            "/api/articles",
            json={
                "title": "revalidate 失敗記錄測試",
                "content_md": "內容",
                "status": "published",
            },
        )
    assert res.status_code == 201
    article = res.json()
    cleanup("articles", article["id"])

    revalidate_records = [r for r in caplog.records if r.name == "app.revalidate"]
    assert revalidate_records, "應該至少有一筆 ISR revalidation 失敗的 log"
    record = revalidate_records[0]
    assert record.slug == article["slug"]
    assert record.error_type
    assert record.content_type == "article"


def test_json_log_formatter_produces_valid_json_with_expected_fields():
    from app.core.logging import _JsonFormatter

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="app.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc-123"
    record.route = "/api/health"
    record.status = 200
    record.duration_ms = 12.3

    parsed = json.loads(formatter.format(record))
    assert parsed["message"] == "request completed"
    assert parsed["request_id"] == "abc-123"
    assert parsed["route"] == "/api/health"
    assert parsed["status"] == 200
    assert parsed["duration_ms"] == 12.3
