import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
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

app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(categories_router)
app.include_router(tags_router)
app.include_router(media_router)
app.include_router(projects_router)
app.include_router(tools_router)
app.include_router(search_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# Serve uploaded media files
os.makedirs(settings.media_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.media_dir), name="uploads")
