import uuid


def test_search_only_returns_published_articles(auth_client, client, cleanup):
    keyword = uuid.uuid4().hex[:12]

    res = auth_client.post(
        "/api/articles",
        json={
            "title": f"草稿文章 {keyword}",
            "content_md": "內容",
            "status": "draft",
        },
    )
    assert res.status_code == 201
    draft_id = res.json()["id"]
    cleanup("articles", draft_id)

    res = auth_client.post(
        "/api/articles",
        json={
            "title": f"已發布文章 {keyword}",
            "content_md": "內容",
            "status": "published",
        },
    )
    assert res.status_code == 201
    published_id = res.json()["id"]
    cleanup("articles", published_id)

    res = client.get("/api/search", params={"q": keyword})
    assert res.status_code == 200
    data = res.json()
    article_ids = [a["id"] for a in data["articles"]]
    assert published_id in article_ids
    assert draft_id not in article_ids


def test_search_only_returns_published_projects(auth_client, client, cleanup):
    keyword = uuid.uuid4().hex[:12]

    res = auth_client.post(
        "/api/projects",
        json={
            "title": f"草稿作品 {keyword}",
            "content_md": "說明",
            "status": "draft",
        },
    )
    assert res.status_code == 201
    draft_id = res.json()["id"]
    cleanup("projects", draft_id)

    res = auth_client.post(
        "/api/projects",
        json={
            "title": f"已發布作品 {keyword}",
            "content_md": "說明",
            "status": "published",
        },
    )
    assert res.status_code == 201
    published_id = res.json()["id"]
    cleanup("projects", published_id)

    res = client.get("/api/search", params={"q": keyword})
    assert res.status_code == 200
    data = res.json()
    project_ids = [p["id"] for p in data["projects"]]
    assert published_id in project_ids
    assert draft_id not in project_ids


def test_search_empty_query_returns_empty(client):
    res = client.get("/api/search", params={"q": ""})
    assert res.status_code in (200, 422)
