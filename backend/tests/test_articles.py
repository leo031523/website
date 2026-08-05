import uuid


def _payload(**overrides):
    unique = uuid.uuid4().hex[:8]
    payload = {
        "title": f"測試文章 {unique}",
        "content_md": "# 內容\n\n測試段落。",
        "status": "draft",
    }
    payload.update(overrides)
    return payload


def test_create_read_update_delete_article(auth_client, cleanup):
    res = auth_client.post("/api/articles", json=_payload())
    assert res.status_code == 201
    article = res.json()
    cleanup("articles", article["id"])
    assert article["status"] == "draft"
    assert article["slug"]

    res = auth_client.get(f"/api/articles/id/{article['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == article["title"]

    res = auth_client.put(f"/api/articles/{article['id']}", json={"title": "更新後標題"})
    assert res.status_code == 200
    assert res.json()["title"] == "更新後標題"

    res = auth_client.delete(f"/api/articles/{article['id']}")
    assert res.status_code == 204

    res = auth_client.get(f"/api/articles/id/{article['id']}")
    assert res.status_code == 404


def test_create_article_requires_login(client):
    res = client.post("/api/articles", json=_payload())
    assert res.status_code == 401


def test_explicit_slug_conflict_rejected(auth_client, cleanup):
    unique = uuid.uuid4().hex[:8]
    slug = f"fixed-slug-{unique}"

    res = auth_client.post("/api/articles", json=_payload(slug=slug))
    assert res.status_code == 201
    cleanup("articles", res.json()["id"])

    res2 = auth_client.post("/api/articles", json=_payload(slug=slug))
    assert res2.status_code == 400


def test_auto_generated_slug_deduplicates(auth_client, cleanup):
    title = f"重複標題 {uuid.uuid4().hex[:8]}"

    res1 = auth_client.post("/api/articles", json=_payload(title=title))
    assert res1.status_code == 201
    cleanup("articles", res1.json()["id"])

    res2 = auth_client.post("/api/articles", json=_payload(title=title))
    assert res2.status_code == 201
    cleanup("articles", res2.json()["id"])

    assert res1.json()["slug"] != res2.json()["slug"]


def test_draft_article_not_visible_to_public(auth_client, client, cleanup):
    res = auth_client.post("/api/articles", json=_payload(status="draft"))
    assert res.status_code == 201
    article = res.json()
    cleanup("articles", article["id"])

    # 未登入無法用 slug 讀到草稿
    res = client.get(f"/api/articles/{article['slug']}")
    assert res.status_code == 404

    # 未登入的列表也不會包含草稿
    res = client.get("/api/articles", params={"page_size": 100})
    assert res.status_code == 200
    slugs = [a["slug"] for a in res.json()["items"]]
    assert article["slug"] not in slugs

    # 已登入的管理者可以看到草稿
    res = auth_client.get(f"/api/articles/{article['slug']}")
    assert res.status_code == 200


def test_published_article_visible_to_public(auth_client, client, cleanup):
    res = auth_client.post("/api/articles", json=_payload(status="published"))
    assert res.status_code == 201
    article = res.json()
    cleanup("articles", article["id"])
    assert article["published_at"] is not None

    res = client.get(f"/api/articles/{article['slug']}")
    assert res.status_code == 200


def test_published_at_only_set_on_first_publish(auth_client, cleanup):
    res = auth_client.post("/api/articles", json=_payload(status="draft"))
    article = res.json()
    cleanup("articles", article["id"])
    assert article["published_at"] is None

    res = auth_client.put(f"/api/articles/{article['id']}", json={"status": "published"})
    first_published_at = res.json()["published_at"]
    assert first_published_at is not None

    res = auth_client.put(f"/api/articles/{article['id']}", json={"title": "再次更新"})
    assert res.json()["published_at"] == first_published_at
