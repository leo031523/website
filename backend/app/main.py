import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api import (
    about_content_router,
    ai_settings_router,
    articles_router,
    auth_router,
    categories_router,
    media_router,
    projects_router,
    search_router,
    tags_router,
    tools_router,
)
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware

configure_logging()
logger = logging.getLogger("app.errors")

app = FastAPI(
    title="Portfolio API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """帳號、slug、email 等 unique constraint 衝突一律回傳 409，不外洩 SQL 細節。"""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "integrity constraint violation",
        extra={
            "request_id": request_id,
            "route": request.url.path,
            "error_type": type(exc.orig).__name__ if exc.orig else type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=409,
        content={"detail": "資料已存在或違反唯一性限制", "request_id": request_id},
    )


app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(categories_router)
app.include_router(tags_router)
app.include_router(media_router)
app.include_router(projects_router)
app.include_router(tools_router)
app.include_router(search_router)
app.include_router(ai_settings_router)
app.include_router(about_content_router)


@app.get("/api/health")
def health():
    """存活檢查（liveness）：process 是否還在跑，不觸碰資料庫。"""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/health/ready")
async def readiness():
    """就緒檢查（readiness）：資料庫是否可連線、可查詢。

    刻意不透過 get_db() 這個 FastAPI dependency 取得連線 ——
    若連線本身失敗（例如資料庫離線），dependency 解析階段就會
    直接拋出例外，根本不會進到這支函式內的 try/except。改為直接
    使用 engine，讓所有連線失敗模式都能在這裡統一被攔截並回傳 503。
    """
    from app.core.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "readiness check failed: database unavailable",
            extra={"error_type": type(exc).__name__},
        )
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unavailable"},
        )
    return {"status": "ok", "database": "ok"}


# Serve uploaded media files
os.makedirs(settings.media_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.media_dir), name="uploads")
