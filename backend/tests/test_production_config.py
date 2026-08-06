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

# 這幾個變數是被測試的對象，子行程的值必須完全由測試案例決定，
# 不能被執行測試的機器/容器本身剛好有設定這幾個變數而悄悄帶過驗證
# （這正是一次真實發生過的 CI 失敗：本機容器因為 docker-compose 的
# .env 而剛好有 AI_MASTER_KEY，測試因此「意外通過」，直到在乾淨的
# CI runner 上才暴露出少更新這個測試檔案的問題）。
_SECRET_ENV_KEYS = {"APP_ENV", "JWT_SECRET", "REVALIDATE_SECRET", "AI_MASTER_KEY", "COOKIE_SECURE"}


def _run_with_env(extra_env: dict) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if k not in _SECRET_ENV_KEYS}
    env = {**base, **_BASE_ENV, **extra_env}
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
            "AI_MASTER_KEY": _STRONG_SECRET,
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
            "AI_MASTER_KEY": _STRONG_SECRET,
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
            "AI_MASTER_KEY": _STRONG_SECRET,
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode != 0
    assert "REVALIDATE_SECRET" in result.stderr


def test_production_rejects_default_ai_master_key():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": _STRONG_SECRET,
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "AI_MASTER_KEY": "change-me-in-production",
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode != 0
    assert "AI_MASTER_KEY" in result.stderr


def test_production_rejects_short_ai_master_key():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": _STRONG_SECRET,
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "AI_MASTER_KEY": "too-short",
            "COOKIE_SECURE": "true",
        }
    )
    assert result.returncode != 0
    assert "AI_MASTER_KEY" in result.stderr


def test_production_rejects_insecure_cookie():
    result = _run_with_env(
        {
            "APP_ENV": "production",
            "JWT_SECRET": _STRONG_SECRET,
            "REVALIDATE_SECRET": _STRONG_SECRET,
            "AI_MASTER_KEY": _STRONG_SECRET,
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
            "AI_MASTER_KEY": _STRONG_SECRET,
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
            "AI_MASTER_KEY": "change-me-in-production",
            "COOKIE_SECURE": "false",
        }
    )
    assert result.returncode == 0, result.stderr
