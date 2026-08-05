import logging

import httpx
import respx

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def _create_settings(auth_client, cleanup, **overrides):
    payload = {"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "real-secret-key-abcd"}
    payload.update(overrides)
    res = auth_client.post("/api/ai/settings", json=payload)
    assert res.status_code == 201
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)
    return settings_id


@respx.mock
def test_connection_test_success(auth_client, cleanup):
    respx.post(_GEMINI_URL).mock(
        return_value=httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        )
    )
    settings_id = _create_settings(auth_client, cleanup)

    res = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["provider"] == "gemini"
    assert data["latency_ms"] is not None
    assert "real-secret-key-abcd" not in res.text


@respx.mock
def test_connection_test_failure_returns_safe_error_category(auth_client, cleanup):
    respx.post(_GEMINI_URL).mock(return_value=httpx.Response(401, json={"error": "denied"}))
    settings_id = _create_settings(auth_client, cleanup)

    res = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["error_category"] == "auth_failed"
    # provider 的原始錯誤內容不應該出現在回應裡
    assert "denied" not in res.text


def test_connection_test_requires_login(client):
    res = client.post("/api/ai/settings/1/test")
    assert res.status_code == 401


def test_connection_test_requires_api_key_configured(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings", json={"provider": "gemini", "model": "gemini-2.0-flash"}
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res.status_code == 400


@respx.mock
def test_connection_test_has_cooldown(auth_client, cleanup):
    respx.post(_GEMINI_URL).mock(
        return_value=httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        )
    )
    settings_id = _create_settings(auth_client, cleanup)

    res1 = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res1.status_code == 200

    res2 = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res2.status_code == 429


@respx.mock
def test_connection_test_never_logs_api_key(auth_client, cleanup, caplog):
    """迴歸測試：httpx 預設會在 INFO 等級記錄外送請求的完整 URL，若
    API key 放在 query string 就會被這行 log 洩漏出去（曾經真的發生
    過，見 app/services/ai/gemini.py 改用 header 傳遞 key 的註解）。

    這裡刻意把 httpx 自己的 logger 等級強制降到 DEBUG，無視
    configure_logging() 預設的 WARNING 抑制 —— 如果 API key 又被
    不小心放回 URL，httpx 內建的 "HTTP Request: ..." log 就會被
    caplog 抓到，測試才會抓到真正的根因回歸，而不是被抑制掉造成
    測試「假通過」。"""
    respx.post(_GEMINI_URL).mock(
        return_value=httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        )
    )
    secret = "leak-canary-key-zz9988"
    settings_id = _create_settings(auth_client, cleanup, api_key=secret)

    with caplog.at_level(logging.DEBUG, logger="httpx"):
        res = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res.status_code == 200

    for record in caplog.records:
        assert secret not in record.getMessage()
        assert secret not in str(record.__dict__)
