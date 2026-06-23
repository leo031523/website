from .articles import router as articles_router
from .auth import router as auth_router
from .categories import router as categories_router
from .media import router as media_router
from .tags import router as tags_router

__all__ = ["auth_router", "articles_router", "categories_router", "tags_router", "media_router"]
