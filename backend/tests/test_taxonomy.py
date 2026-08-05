import uuid

import pytest


@pytest.mark.parametrize("resource", ["categories", "tags"])
def test_create_read_update_delete(auth_client, cleanup, resource):
    unique = uuid.uuid4().hex[:8]
    payload = {"name": f"分類-{unique}", "slug": f"slug-{unique}"}

    res = auth_client.post(f"/api/{resource}", json=payload)
    assert res.status_code == 201
    item = res.json()
    cleanup(resource, item["id"])
    assert item["slug"] == payload["slug"]

    res = auth_client.get(f"/api/{resource}")
    assert res.status_code == 200
    assert any(i["id"] == item["id"] for i in res.json())

    res = auth_client.put(f"/api/{resource}/{item['id']}", json={"name": "更新後名稱"})
    assert res.status_code == 200
    assert res.json()["name"] == "更新後名稱"

    res = auth_client.delete(f"/api/{resource}/{item['id']}")
    assert res.status_code == 204

    res = auth_client.get(f"/api/{resource}")
    assert item["id"] not in [i["id"] for i in res.json()]


@pytest.mark.parametrize("resource", ["categories", "tags"])
def test_duplicate_slug_rejected(auth_client, cleanup, resource):
    unique = uuid.uuid4().hex[:8]
    payload = {"name": f"分類-{unique}", "slug": f"dup-slug-{unique}"}

    res1 = auth_client.post(f"/api/{resource}", json=payload)
    assert res1.status_code == 201
    cleanup(resource, res1.json()["id"])

    res2 = auth_client.post(f"/api/{resource}", json=payload)
    assert res2.status_code == 400


@pytest.mark.parametrize("resource", ["categories", "tags"])
def test_write_requires_login(client, resource):
    res = client.post(f"/api/{resource}", json={"name": "x", "slug": "x"})
    assert res.status_code == 401


def test_tool_create_read_update_delete(auth_client, cleanup):
    unique = uuid.uuid4().hex[:8]
    payload = {"name": f"工具-{unique}", "category": "後端"}

    res = auth_client.post("/api/tools", json=payload)
    assert res.status_code == 201
    tool = res.json()
    cleanup("tools", tool["id"])

    res = auth_client.put(f"/api/tools/{tool['id']}", json={"name": "更新後工具名稱"})
    assert res.status_code == 200
    assert res.json()["name"] == "更新後工具名稱"

    res = auth_client.delete(f"/api/tools/{tool['id']}")
    assert res.status_code == 204

    res = auth_client.get("/api/tools")
    assert tool["id"] not in [t["id"] for t in res.json()]


def test_tool_write_requires_login(client):
    res = client.post("/api/tools", json={"name": "x"})
    assert res.status_code == 401
