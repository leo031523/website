"""驗證 APP_ENV=production 下，不安全的設定會讓應用程式拒絕啟動。

用子行程重新匯入 app.core.config，避免影響同一個行程內其他測試
已經建立好的 Settings 單例（Settings 只在模組匯入當下讀取一次環境變數）。
"""

import os
import subprocess
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent

_BASE_ENV = {
    "DATABASE_URL": "postgresql://portfolio:test@localhost:5432/portfolio_db",
    "MEDIA_DIR": "/tmp/test-media",
}

_STRONG_SECRET = "a" * 40


def _run_with_env(extra_env: dict) -> subprocess.CompletedProcess:
    env = {**os.environ, **_BASE_ENV, **extra_env}
    return subprocess.run(
        [sys.executable, "-c", "from app.core.config import settings"],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_production_rejects_default_jwt_secret():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": "change-me-in-production",
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode != 0
    assert "JWT_SECRET" in result.stderr


def test_production_rejects_short_secret():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": "too-short",
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode != 0
    assert "JWT_SECRET" in result.stderr


def test_production_rejects_default_revalidate_secret():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": _STRONG_SECRET,
            "REVALIDATE_SECRET": "change-me-in-production",
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode != 0
    assert "REVALIDATE_SECRET" in result.stderr


def test_production_rejects_insecure_cookie():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": _STRONG_SECRET,
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "COOKIE_SECURE": "false",
        }
    )
    assert result.returncode != 0
    assert "COOKIE_SECURE" in result.stderr


def test_production_accepts_strong_config():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": _STRONG_SECRET,
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode == 0, result.stderr


def test_development_allows_default_secrets():
    result = _run_with_env(
        {
            "APP_ENV": "development",
            "JWT_SECRET": "change-me-in-production",
            "REVALIDATE_SECRET": "change-me-in-production",
            "COOKIE_SECURE": "false",
        }
    )
    assert result.returncode == 0, result.stderr
