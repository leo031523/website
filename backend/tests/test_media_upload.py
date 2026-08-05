import io
import os
import shutil

os.environ.setdefault("DATABASE_URL", "postgresql://portfolio:test@localhost:5432/portfolio_db")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-key-must-be-32-chars!")
os.environ.setdefault("MEDIA_DIR", "/tmp/test-media")

import psycopg2  # noqa: E402
import pytest  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

# 直接用同步的 psycopg2 操作測試資料，避免與 TestClient/asyncpg
# 各自建立的 event loop 互相衝突（見 SQLAlchemy async engine 綁定
# event loop 的限制）。

TEST_USERNAME = "media_test_admin"
TEST_EMAIL = "media_test_admin@example.com"
TEST_PASSWORD = "test-password-123"


def _create_test_user():
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (TEST_USERNAME,))
            if cur.fetchone():
                return
            cur.execute(
                "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)",
                (TEST_USERNAME, TEST_EMAIL, hash_password(TEST_PASSWORD)),
            )
    finally:
        conn.close()


def _delete_test_user():
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE username = %s", (TEST_USERNAME,))
    finally:
        conn.close()


def _delete_all_test_media():
    conn = psycopg2.connect(settings.database_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT path FROM media")
            paths = [row[0] for row in cur.fetchall()]
            for p in paths:
                if os.path.exists(p):
                    os.remove(p)
            cur.execute("DELETE FROM media")
    finally:
        conn.close()


@pytest.fixture(scope="module", autouse=True)
def _media_dir():
    os.makedirs("/tmp/test-media", exist_ok=True)
    yield
    shutil.rmtree("/tmp/test-media", ignore_errors=True)


@pytest.fixture(scope="module")
def auth_client():
    _create_test_user()
    client = TestClient(app)
    res = client.post("/api/auth/login", json={"username": TEST_USERNAME, "password": TEST_PASSWORD})
    assert res.status_code == 200
    yield client
    _delete_all_test_media()
    _delete_test_user()


def _image_bytes(fmt: str, mode: str = "RGB", size: tuple[int, int] = (64, 64)) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, color=(200, 50, 50) if mode == "RGB" else (200, 50, 50, 128)).save(buf, format=fmt)
    return buf.getvalue()


@pytest.mark.parametrize(
    "fmt,mode,content_type,filename",
    [
        ("JPEG", "RGB", "image/jpeg", "photo.jpg"),
        ("PNG", "RGBA", "image/png", "photo.png"),
        ("GIF", "RGB", "image/gif", "photo.gif"),
        ("WEBP", "RGBA", "image/webp", "photo.webp"),
    ],
)
def test_upload_valid_image_succeeds(auth_client, fmt, mode, content_type, filename):
    contents = _image_bytes(fmt, mode)
    res = auth_client.post(
        "/api/media",
        files={"file": (filename, contents, content_type)},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["mime_type"] == content_type
    auth_client.delete(f"/api/media/{data['id']}")


def test_upload_rejects_html_disguised_as_jpeg(auth_client):
    fake = b"<html><body><script>alert(1)</script></body></html>"
    res = auth_client.post(
        "/api/media",
        files={"file": ("fake.jpg", fake, "image/jpeg")},
    )
    assert res.status_code == 400


def test_upload_rejects_plain_text_disguised_as_png(auth_client):
    fake = b"just plain text, not an image at all"
    res = auth_client.post(
        "/api/media",
        files={"file": ("fake.png", fake, "image/png")},
    )
    assert res.status_code == 400


def test_upload_rejects_truncated_corrupted_image(auth_client):
    contents = _image_bytes("PNG", "RGBA")
    truncated = contents[: len(contents) // 2]
    res = auth_client.post(
        "/api/media",
        files={"file": ("broken.png", truncated, "image/png")},
    )
    assert res.status_code == 400


def test_upload_ignores_client_supplied_extension(auth_client):
    """真正的 PNG 內容但檔名/Content-Type 偽裝成 jpg，仍應以實際內容判斷格式。"""
    contents = _image_bytes("PNG", "RGBA")
    res = auth_client.post(
        "/api/media",
        files={"file": ("actually-a-png.jpg", contents, "image/jpeg")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["mime_type"] == "image/png"
    assert data["url"].endswith(".png")
    auth_client.delete(f"/api/media/{data['id']}")


def test_upload_rejects_oversized_file(auth_client):
    big = b"\xff\xd8\xff" + os.urandom(10 * 1024 * 1024 + 1)
    res = auth_client.post(
        "/api/media",
        files={"file": ("big.jpg", big, "image/jpeg")},
    )
    assert res.status_code == 400


def test_upload_requires_login():
    unauthenticated = TestClient(app)
    contents = _image_bytes("JPEG", "RGB")
    res = unauthenticated.post(
        "/api/media",
        files={"file": ("photo.jpg", contents, "image/jpeg")},
    )
    assert res.status_code == 401


def test_delete_requires_login():
    unauthenticated = TestClient(app)
    res = unauthenticated.delete("/api/media/1")
    assert res.status_code == 401
