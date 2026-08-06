from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_DEFAULT = "change-me-in-production"
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://portfolio:password@db:5432/portfolio_db"
    jwt_secret: str = _INSECURE_DEFAULT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost"
    revalidate_secret: str = _INSECURE_DEFAULT
    frontend_url: str = "http://frontend:3000"
    media_dir: str = "/app/media"
    # 正式環境務必設為 true，讓登入 Cookie 帶有 Secure 屬性（僅透過 HTTPS 傳送）
    cookie_secure: bool = False
    # 用來加密 AI provider API key 的 master key；遺失即無法解密已存的 key，
    # 只能請管理者重新輸入一次。
    ai_master_key: str = _INSECURE_DEFAULT
    # 正式環境預設拒絕 OpenAI-compatible provider 的 base_url 指向
    # loopback／內網／metadata 位址（SSRF 防護）。若部署情境確實需要
    # 連線到內網的自架模型，把主機名稱加進這個逗號分隔的白名單。
    ai_local_model_allowlist: str = ""

    model_config = {"env_file": ".env"}

    @model_validator(mode="after")
    def _reject_insecure_production_config(self) -> "Settings":
        if self.app_env != "production":
            return self

        problems = []
        if self.jwt_secret == _INSECURE_DEFAULT or len(self.jwt_secret) < _MIN_SECRET_LENGTH:
            problems.append(f"JWT_SECRET 必須設定為至少 {_MIN_SECRET_LENGTH} 字元的隨機字串")
        if self.revalidate_secret == _INSECURE_DEFAULT or len(self.revalidate_secret) < _MIN_SECRET_LENGTH:
            problems.append(f"REVALIDATE_SECRET 必須設定為至少 {_MIN_SECRET_LENGTH} 字元的隨機字串")
        if self.ai_master_key == _INSECURE_DEFAULT or len(self.ai_master_key) < _MIN_SECRET_LENGTH:
            problems.append(f"AI_MASTER_KEY 必須設定為至少 {_MIN_SECRET_LENGTH} 字元的隨機字串")
        if not self.cookie_secure:
            problems.append("COOKIE_SECURE 必須設為 true（正式環境的登入 Cookie 需要 Secure 屬性）")

        if problems:
            raise ValueError(
                "APP_ENV=production 但設定不安全，拒絕啟動：\n- " + "\n- ".join(problems)
            )
        return self


settings = Settings()
