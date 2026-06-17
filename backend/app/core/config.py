from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://portfolio:password@db:5432/portfolio_db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: list[str] = ["http://localhost"]
    revalidate_secret: str = "change-me-in-production"

    model_config = {"env_file": ".env"}


settings = Settings()
