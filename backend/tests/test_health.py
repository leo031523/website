import os

# Set env vars before any app imports so Settings() picks them up
os.environ.setdefault("DATABASE_URL", "postgresql://portfolio:test@localhost:5432/portfolio_db")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-key-must-be-32-chars!")
os.environ.setdefault("MEDIA_DIR", "/tmp/test-media")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_login_wrong_password():
    res = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
    assert res.status_code == 401
