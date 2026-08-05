import io
import os
import shutil

import pytest
from PIL import Image


@pytest.fixture(scope="module", autouse=True)
def _media_dir():
    os.makedirs("/tmp/test-media", exist_ok=True)
    yield
    shutil.rmtree("/tmp/test-media", ignore_errors=True)


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


def test_upload_requires_login(client):
    contents = _image_bytes("JPEG", "RGB")
    res = client.post(
        "/api/media",
        files={"file": ("photo.jpg", contents, "image/jpeg")},
    )
    assert res.status_code == 401


def test_delete_requires_login(client):
    res = client.delete("/api/media/1")
    assert res.status_code == 401
