def test_get_about_returns_seeded_content(client):
    """migration 005 已經 seed 了一筆 id=1 的內容，公開端點應該能讀到。"""
    res = client.get("/api/about")
    assert res.status_code == 200
    data = res.json()
    assert data["content_md"]
    assert "updated_at" in data


def test_update_about_requires_login(client):
    res = client.put("/api/about", json={"content_md": "駭進來的內容"})
    assert res.status_code == 401


def test_update_about_changes_content_and_is_publicly_visible(auth_client, client):
    original = client.get("/api/about").json()["content_md"]
    try:
        new_content = "更新後的關於我內容 " + "x" * 10
        res = auth_client.put("/api/about", json={"content_md": new_content})
        assert res.status_code == 200
        assert res.json()["content_md"] == new_content

        res = client.get("/api/about")
        assert res.status_code == 200
        assert res.json()["content_md"] == new_content
    finally:
        auth_client.put("/api/about", json={"content_md": original})


def test_update_about_persists_across_requests(auth_client, client):
    original = client.get("/api/about").json()["content_md"]
    try:
        auth_client.put("/api/about", json={"content_md": "第一次更新"})
        res = auth_client.put("/api/about", json={"content_md": "第二次更新"})
        assert res.status_code == 200
        assert res.json()["content_md"] == "第二次更新"

        res = client.get("/api/about")
        assert res.json()["content_md"] == "第二次更新"
    finally:
        auth_client.put("/api/about", json={"content_md": original})
