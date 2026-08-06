import os

# 在任何 app 模組被匯入前先設定測試環境變數，讓 Settings() 讀到正確的值。
# conftest.py 保證比同目錄下的測試檔案更早被 pytest 載入。
os.environ.setdefault("DATABASE_URL", "postgresql://portfolio:test@localhost:5432/portfolio_db")
os.environ.setdefault("JWT_SECRET", "ci-test-secret-key-must-be-32-chars!")
os.environ.setdefault("MEDIA_DIR", "/tmp/test-media")

import uuid  # noqa: E402
from collections.abc import Iterator  # noqa: E402

import psycopg2  # noqa: E402
import pytest  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

TEST_PASSWORD = "test-password-123"


@pytest.fixture
def db_conn() -> Iterator[psycopg2.extensions.connection]:
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
async def db_session():
    """給需要直接呼叫 async service 層函式（不透過 HTTP API）的測試用。
    沿用 app 自己的 SessionLocal，測試環境下已經是 NullPool，
    不會有 TestClient 跨 event loop 重用連線的問題。"""
    from app.core.database import SessionLocal

    async with SessionLocal() as session:
        yield session


@pytest.fixture
def admin_user(db_conn) -> Iterator[dict]:
    """建立一個獨立、隨機命名的測試管理者帳號，測試結束後自動刪除。

    每個測試都拿到不同帳號，避免測試之間互相依賴或污染彼此資料。
    """
    username = f"test_{uuid.uuid4().hex[:16]}"
    email = f"{username}@example.com"
    with db_conn, db_conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s) RETURNING id",
            (username, email, hash_password(TEST_PASSWORD)),
        )
        user_id = cur.fetchone()[0]

    yield {"id": user_id, "username": username, "email": email, "password": TEST_PASSWORD}

    with db_conn, db_conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


@pytest.fixture
def auth_client(admin_user) -> TestClient:
    """已登入的 TestClient，帳號隨測試結束自動清除。

    登入端點有 per-IP 速率限制（防暴力破解），但 TestClient 預設的
    client host 固定是 "testclient"——如果不重置，整個測試套件裡
    每一個用到這個 fixture 的測試都會疊加同一個配額，很快就會被自己
    的測試觸發 429。這裡在登入前重置，讓每個測試各自獨立。
    """
    import app.api.auth as auth_module

    auth_module._login_rate_limiter.reset("testclient")

    c = TestClient(app)
    res = c.post(
        "/api/auth/login",
        json={"username": admin_user["username"], "password": admin_user["password"]},
    )
    assert res.status_code == 200
    return c


@pytest.fixture
def cleanup(db_conn):
    """測試可呼叫 cleanup("table_name", id) 註冊建立過的資料列，
    測試結束後依註冊的反序刪除（後建立的先刪，符合常見的 FK 相依順序）。
    """
    items: list[tuple[str, int]] = []

    def _register(table: str, row_id: int) -> None:
        items.append((table, row_id))

    yield _register

    with db_conn, db_conn.cursor() as cur:
        for table, row_id in reversed(items):
            cur.execute(f"DELETE FROM {table} WHERE id = %s", (row_id,))  # noqa: S608
