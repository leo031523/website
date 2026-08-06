import uuid

import httpx
import respx
from app.services.ai.rate_limit import reset_rate_limit

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Starlette TestClient 在沒有額外設定時，request.client.host 固定是
# "testclient"；我們的 rate limiter 用它當 key，所以每個會呼叫
# /api/ai/chat 的測試都要在結束後重置，避免測試互相干擾彼此的配額。
_TEST_CLIENT_KEY = "testclient"


def _gemini_success(text: str):
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})


def _enable_gemini(auth_client, cleanup, api_key="test-gemini-key-1234"):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": api_key},
    )
    assert res.status_code == 201
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)
    res = auth_client.post(f"/api/ai/settings/{settings_id}/enable")
    assert res.status_code == 200
    return settings_id


def _publish_article(auth_client, cleanup, keyword: str, content_suffix: str = ""):
    res = auth_client.post(
        "/api/articles",
        json={
            "title": f"聊天測試文章 {keyword}",
            "content_md": f"這篇文章介紹 {keyword} 相關的技術細節。{content_suffix}",
            "status": "published",
        },
    )
    assert res.status_code == 201
    article = res.json()
    cleanup("articles", article["id"])
    return article


def _keyword() -> str:
    return f"測試主題{uuid.uuid4().hex[:8]}"


def test_chat_rejects_empty_message(client):
    res = client.post("/api/ai/chat", json={"message": "   "})
    assert res.status_code == 422


def test_chat_rejects_oversized_message(client):
    res = client.post("/api/ai/chat", json={"message": "字" * 2001})
    assert res.status_code == 422


def test_chat_rejects_too_many_history_turns(client):
    history = [{"role": "user", "content": "hi"} for _ in range(11)]
    res = client.post("/api/ai/chat", json={"message": "問題", "history": history})
    assert res.status_code == 422


def test_chat_rejects_invalid_history_role(client):
    res = client.post(
        "/api/ai/chat",
        json={"message": "問題", "history": [{"role": "system", "content": "x"}]},
    )
    assert res.status_code == 422


def test_chat_returns_503_when_no_provider_enabled(client):
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        res = client.post("/api/ai/chat", json={"message": _keyword()})
        assert res.status_code == 503
        assert "request_id" in res.json()
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_returns_ungrounded_fallback_when_no_content_matches(auth_client, cleanup, client):
    _enable_gemini(auth_client, cleanup)
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        res = client.post("/api/ai/chat", json={"message": _keyword()})
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert data["sources"] == []
        assert "沒有足夠資訊" in data["answer"]
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_returns_grounded_answer_with_valid_citation(auth_client, cleanup, client):
    keyword = _keyword()
    article = _publish_article(auth_client, cleanup, keyword)
    _enable_gemini(auth_client, cleanup)
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        chunk_id = f"article:{article['id']}#chunk-0"
        respx.post(_GEMINI_URL).mock(
            return_value=_gemini_success(f"這是關於{keyword}的說明 [來源: {chunk_id}]。")
        )

        res = client.post("/api/ai/chat", json={"message": keyword})
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is True
        assert len(data["sources"]) == 1
        assert data["sources"][0]["id"] == chunk_id
        assert data["sources"][0]["url"] == f"/blog/{article['slug']}"
        assert "request_id" in data
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_downgrades_to_fallback_when_model_hallucinates_source(auth_client, cleanup, client):
    """模型引用了不存在的 source id（幻覺），後端必須降級成明確拒答，
    不能把沒有真實依據的回答原封不動回給使用者。"""
    keyword = _keyword()
    _publish_article(auth_client, cleanup, keyword)
    _enable_gemini(auth_client, cleanup)
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        respx.post(_GEMINI_URL).mock(
            return_value=_gemini_success("這是答案 [來源: article:999999#chunk-0]。")
        )

        res = client.post("/api/ai/chat", json={"message": keyword})
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert data["sources"] == []
        assert "沒有足夠資訊" in data["answer"]
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_never_returns_draft_article_content(auth_client, cleanup, client):
    keyword = _keyword()
    res = auth_client.post(
        "/api/articles",
        json={
            "title": "草稿不該被聊天功能看到",
            "content_md": f"這是關於 {keyword} 的機密草稿內容。",
            "status": "draft",
        },
    )
    assert res.status_code == 201
    cleanup("articles", res.json()["id"])
    _enable_gemini(auth_client, cleanup)
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        res = client.post("/api/ai/chat", json={"message": keyword})
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert "機密草稿" not in data["answer"]
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_handles_provider_auth_failure_without_leaking_details(auth_client, cleanup, client):
    keyword = _keyword()
    _publish_article(auth_client, cleanup, keyword)
    _enable_gemini(auth_client, cleanup, api_key="invalid-key")
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        respx.post(_GEMINI_URL).mock(
            return_value=httpx.Response(
                401, json={"error": {"message": "sensitive internal detail", "code": 401}}
            )
        )

        res = client.post("/api/ai/chat", json={"message": keyword})
        assert res.status_code == 502
        assert "sensitive internal detail" not in res.text
        assert "invalid-key" not in res.text
        assert "request_id" in res.json()
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_handles_provider_timeout(auth_client, cleanup, client):
    keyword = _keyword()
    _publish_article(auth_client, cleanup, keyword)
    _enable_gemini(auth_client, cleanup)
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        respx.post(_GEMINI_URL).mock(side_effect=httpx.TimeoutException("boom"))

        res = client.post("/api/ai/chat", json={"message": keyword})
        assert res.status_code == 504
        assert "request_id" in res.json()
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


def test_chat_rate_limit_blocks_after_threshold(auth_client, cleanup, client):
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        for _ in range(10):
            res = client.post("/api/ai/chat", json={"message": _keyword()})
            assert res.status_code in (200, 503)  # 沒開 provider 時是 503，這裡只測配額本身
        res = client.post("/api/ai/chat", json={"message": _keyword()})
        assert res.status_code == 429
        assert "request_id" in res.json()
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)


@respx.mock
def test_chat_response_never_contains_api_key(auth_client, cleanup, client):
    keyword = _keyword()
    article = _publish_article(auth_client, cleanup, keyword)
    secret = "canary-secret-key-778899"
    _enable_gemini(auth_client, cleanup, api_key=secret)
    reset_rate_limit(_TEST_CLIENT_KEY)
    try:
        chunk_id = f"article:{article['id']}#chunk-0"
        respx.post(_GEMINI_URL).mock(
            return_value=_gemini_success(f"回答內容 [來源: {chunk_id}]。")
        )

        res = client.post("/api/ai/chat", json={"message": keyword})
        assert res.status_code == 200
        assert secret not in res.text
    finally:
        reset_rate_limit(_TEST_CLIENT_KEY)
