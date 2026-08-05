def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
    assert res.status_code == 401
