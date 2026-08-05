import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_engine_kwargs: dict = {"echo": False}
if "PYTEST_VERSION" in os.environ:
    # 測試時每個 TestClient 呼叫可能使用不同的 event loop，若沿用連線池，
    # 舊 loop 綁定的 asyncpg 連線會在下一個 loop 中失效並拋出例外。
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(_async_url(settings.database_url), **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
