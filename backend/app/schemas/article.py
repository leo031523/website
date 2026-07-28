from datetime import datetime

from pydantic import BaseModel

from app.models.article import ArticleStatus
from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse


class ArticleCreate(BaseModel):
    title: str
    slug: str | None = None
    excerpt: str | None = None
    content_md: str
    status: ArticleStatus = ArticleStatus.draft
    category_id: int | None = None
    tag_ids: list[int] = []
    cover_image_id: int | None = None


class ArticleUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    content_md: str | None = None
    status: ArticleStatus | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None
    cover_image_id: int | None = None


class ArticleListItem(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str | None
    status: ArticleStatus
    published_at: datetime | None
    category: CategoryResponse | None
    tags: list[TagResponse]
    cover_image_id: int | None
    cover_image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArticleResponse(ArticleListItem):
    content_md: str
    author_id: int
