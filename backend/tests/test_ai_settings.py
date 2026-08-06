def test_create_ai_settings_never_returns_plaintext_key(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "secret-key-abcdef1234"},
    )
    assert res.status_code == 201
    data = res.json()
    cleanup("ai_provider_settings", data["id"])

    assert data["is_configured"] is True
    assert data["api_key_suffix"] == "****1234"
    assert "secret-key-abcdef1234" not in res.text
    assert "encrypted_api_key" not in data


def test_create_requires_login(client):
    res = client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash"},
    )
    assert res.status_code == 401


def test_openai_compatible_requires_base_url(auth_client):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "openai_compatible", "model": "llama3"},
    )
    assert res.status_code == 422


def test_non_compatible_provider_rejects_base_url(auth_client):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "base_url": "http://localhost:11434"},
    )
    assert res.status_code == 422


def test_list_settings_shows_masked_suffix_of_currently_stored_key(auth_client, cleanup):
    """遮罩尾碼不是只有建立當下才看得到——管理者事後重新整理頁面、
    再次讀取設定列表時，也要能看到目前生效的是哪把 key（遮罩後），
    而不是永遠顯示 null，逼管理者只能靠記憶或重新輸入才能確認。"""
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "secret-xyz-7890"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.get("/api/ai/settings")
    assert res.status_code == 200
    row = next(s for s in res.json() if s["id"] == settings_id)
    assert row["api_key_suffix"] == "****7890"
    assert "secret-xyz-7890" not in res.text


def test_list_settings_never_leaks_encrypted_key_field(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "secret-abc123"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.get("/api/ai/settings")
    assert res.status_code == 200
    assert "secret-abc123" not in res.text
    assert "encrypted_api_key" not in res.text


def test_update_blank_api_key_keeps_existing_key(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "original-key-1234"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.put(f"/api/ai/settings/{settings_id}", json={"model": "gemini-2.0-pro"})
    assert res.status_code == 200
    data = res.json()
    assert data["model"] == "gemini-2.0-pro"
    assert data["is_configured"] is True


def test_update_with_remove_api_key_clears_it(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "original-key-1234"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.put(f"/api/ai/settings/{settings_id}", json={"remove_api_key": True})
    assert res.status_code == 200
    assert res.json()["is_configured"] is False


def test_enable_requires_api_key(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.post(f"/api/ai/settings/{settings_id}/enable")
    assert res.status_code == 400


def test_enabling_one_provider_disables_others(auth_client, cleanup):
    res1 = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "key-one-1234"},
    )
    id1 = res1.json()["id"]
    cleanup("ai_provider_settings", id1)

    res2 = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-1.5-flash", "api_key": "key-two-5678"},
    )
    id2 = res2.json()["id"]
    cleanup("ai_provider_settings", id2)

    res = auth_client.post(f"/api/ai/settings/{id1}/enable")
    assert res.status_code == 200
    assert res.json()["is_enabled"] is True

    res = auth_client.post(f"/api/ai/settings/{id2}/enable")
    assert res.status_code == 200
    assert res.json()["is_enabled"] is True

    res = auth_client.get("/api/ai/settings")
    enabled = [s for s in res.json() if s["is_enabled"]]
    assert len(enabled) == 1
    assert enabled[0]["id"] == id2


def test_enable_rejects_unsupported_provider(auth_client, cleanup, monkeypatch):
    """/enable 必須先確認 provider 有真的 adapter 實作，不能等到啟用後
    第一次真正呼叫聊天 API 才發現整個 adapter 不存在、讓使用者收到未
    處理的例外。用 monkeypatch 模擬「這個 provider 還沒有 adapter」的
    情境來測 guard 本身的邏輯，不綁定在目前剛好哪家還沒做完。"""
    import app.api.ai_settings as ai_settings_module

    monkeypatch.setattr(ai_settings_module, "SUPPORTED_PROVIDERS", frozenset())

    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "key-1234"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.post(f"/api/ai/settings/{settings_id}/enable")
    assert res.status_code == 400


def test_test_connection_rejects_unsupported_provider(auth_client, cleanup, monkeypatch):
    import app.api.ai_settings as ai_settings_module

    monkeypatch.setattr(ai_settings_module, "SUPPORTED_PROVIDERS", frozenset())

    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash", "api_key": "key-1234"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.post(f"/api/ai/settings/{settings_id}/test")
    assert res.status_code == 400


def test_all_declared_providers_have_adapters():
    """四種 provider（Gemini／OpenAI／Claude／OpenAI-compatible）現在都
    有實際的 adapter 實作了；這條測試釘住這個狀態，未來如果新增第五種
    provider enum 卻忘記寫 adapter，這裡會先失敗提醒，而不是等使用者
    在後台啟用後才發現。"""
    from app.models.ai_settings import AIProvider
    from app.services.ai.registry import SUPPORTED_PROVIDERS

    assert SUPPORTED_PROVIDERS == frozenset(AIProvider)


def test_delete_settings(auth_client, cleanup):
    res = auth_client.post(
        "/api/ai/settings",
        json={"provider": "gemini", "model": "gemini-2.0-flash"},
    )
    settings_id = res.json()["id"]
    cleanup("ai_provider_settings", settings_id)

    res = auth_client.delete(f"/api/ai/settings/{settings_id}")
    assert res.status_code == 204

    res = auth_client.get("/api/ai/settings")
    assert settings_id not in [s["id"] for s in res.json()]
