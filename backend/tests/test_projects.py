import uuid


def _payload(**overrides):
    unique = uuid.uuid4().hex[:8]
    payload = {
        "title": f"測試作品 {unique}",
        "content_md": "# 作品說明",
        "status": "draft",
    }
    payload.update(overrides)
    return payload


def test_create_read_update_delete_project(auth_client, cleanup):
    res = auth_client.post("/api/projects", json=_payload())
    assert res.status_code == 201
    project = res.json()
    cleanup("projects", project["id"])
    assert project["status"] == "draft"
    assert project["slug"]

    res = auth_client.get(f"/api/projects/id/{project['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == project["title"]

    res = auth_client.put(f"/api/projects/{project['id']}", json={"title": "更新後作品標題"})
    assert res.status_code == 200
    assert res.json()["title"] == "更新後作品標題"

    res = auth_client.delete(f"/api/projects/{project['id']}")
    assert res.status_code == 204

    res = auth_client.get(f"/api/projects/id/{project['id']}")
    assert res.status_code == 404


def test_create_project_requires_login(client):
    res = client.post("/api/projects", json=_payload())
    assert res.status_code == 401


def test_explicit_slug_conflict_rejected(auth_client, cleanup):
    unique = uuid.uuid4().hex[:8]
    slug = f"fixed-project-slug-{unique}"

    res = auth_client.post("/api/projects", json=_payload(slug=slug))
    assert res.status_code == 201
    cleanup("projects", res.json()["id"])

    res2 = auth_client.post("/api/projects", json=_payload(slug=slug))
    assert res2.status_code == 400


def test_auto_generated_slug_deduplicates(auth_client, cleanup):
    title = f"重複作品標題 {uuid.uuid4().hex[:8]}"

    res1 = auth_client.post("/api/projects", json=_payload(title=title))
    assert res1.status_code == 201
    cleanup("projects", res1.json()["id"])

    res2 = auth_client.post("/api/projects", json=_payload(title=title))
    assert res2.status_code == 201
    cleanup("projects", res2.json()["id"])

    assert res1.json()["slug"] != res2.json()["slug"]


def test_draft_project_not_visible_to_public(auth_client, client, cleanup):
    res = auth_client.post("/api/projects", json=_payload(status="draft"))
    assert res.status_code == 201
    project = res.json()
    cleanup("projects", project["id"])

    res = client.get(f"/api/projects/{project['slug']}")
    assert res.status_code == 404

    res = client.get("/api/projects")
    assert res.status_code == 200
    slugs = [p["slug"] for p in res.json()]
    assert project["slug"] not in slugs

    res = auth_client.get(f"/api/projects/{project['slug']}")
    assert res.status_code == 200


def test_published_project_visible_to_public(auth_client, client, cleanup):
    res = auth_client.post("/api/projects", json=_payload(status="published"))
    assert res.status_code == 201
    project = res.json()
    cleanup("projects", project["id"])

    res = client.get(f"/api/projects/{project['slug']}")
    assert res.status_code == 200
