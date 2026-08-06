from .about_content import router as about_content_router
from .ai_settings import router as ai_settings_router
from .articles import router as articles_router
from .auth import router as auth_router
from .categories import router as categories_router
from .media import router as media_router
from .projects import router as projects_router
from .search import router as search_router
from .tags import router as tags_router
from .tools import router as tools_router

__all__ = [
    "auth_router",
    "articles_router",
    "categories_router",
    "tags_router",
    "media_router",
    "projects_router",
    "tools_router",
    "search_router",
    "ai_settings_router",
    "about_content_router",
]
