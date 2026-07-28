import math
import re
import unicodedata
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.article import Article, ArticleStatus
from app.models.tag import Tag, article_tags
from app.models.user import User
from app.schemas.article import (
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleUpdate,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _slugify(title: str) -> str:
    slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = slug.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-") or "article"


async def _unique_slug(slug: str, db: AsyncSession, exclude_id: int | None = None) -> str:
    base, counter = slug, 1
    while True:
        q = select(Article).where(Article.slug == slug)
        if exclude_id is not None:
            q = q.where(Article.id != exclude_id)
        if not (await db.execute(q)).scalar_one_or_none():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


async def _trigger_revalidate(slug: str) -> None:
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.frontend_url}/api/revalidate",
                json={"slug": slug, "secret": settings.revalidate_secret},
                timeout=5.0,
            )
    except Exception:
        pass


def _load_options():
    return [
        selectinload(Article.category),
        selectinload(Article.tags),
        selectinload(Article.cover_image),
    ]


@router.get("/id/{article_id}", response_model=ArticleResponse)
async def get_article_by_id(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Article).options(*_load_options()).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="找不到文章")
    return article


@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None),
    tag_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    conditions = []
    if current_user is None:
        conditions.append(Article.status == ArticleStatus.published)
    if category_id is not None:
        conditions.append(Article.category_id == category_id)
    if tag_id is not None:
        conditions.append(
            exists().where(
                article_tags.c.article_id == Article.id,
                article_tags.c.tag_id == tag_id,
            )
        )

    count_q = select(func.count(Article.id))
    if conditions:
        count_q = count_q.where(*conditions)
    total: int = (await db.execute(count_q)).scalar() or 0

    stmt = (
        select(Article)
        .options(*_load_options())
        .order_by(Article.published_at.desc().nulls_last(), Article.created_at.desc())
    )
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(stmt)).scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    stmt = select(Article).options(*_load_options()).where(Article.slug == slug)
    if current_user is None:
        stmt = stmt.where(Article.status == ArticleStatus.published)
    article = (await db.execute(stmt)).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="找不到文章")
    return article


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.slug:
        existing = (await db.execute(select(Article).where(Article.slug == body.slug))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="slug 已存在")
        slug = body.slug
    else:
        slug = await _unique_slug(_slugify(body.title), db)

    article = Article(
        title=body.title,
        slug=slug,
        excerpt=body.excerpt,
        content_md=body.content_md,
        status=body.status,
        category_id=body.category_id,
        cover_image_id=body.cover_image_id,
        author_id=current_user.id,
    )
    if body.status == ArticleStatus.published:
        article.published_at = datetime.now(timezone.utc)

    if body.tag_ids:
        tags = (await db.execute(select(Tag).where(Tag.id.in_(body.tag_ids)))).scalars().all()
        article.tags = list(tags)

    db.add(article)
    await db.commit()

    result = await db.execute(
        select(Article).options(*_load_options()).where(Article.id == article.id)
    )
    article = result.scalar_one()

    if article.status == ArticleStatus.published:
        await _trigger_revalidate(article.slug)

    return article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    body: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Article).options(*_load_options()).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="找不到文章")

    was_published = article.status == ArticleStatus.published
    update_data = body.model_dump(exclude_none=True)
    tag_ids = update_data.pop("tag_ids", None)

    if "slug" in update_data and update_data["slug"] != article.slug:
        conflict = (
            await db.execute(
                select(Article).where(
                    Article.slug == update_data["slug"], Article.id != article_id
                )
            )
        ).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=400, detail="slug 已存在")

    for field, value in update_data.items():
        setattr(article, field, value)

    if tag_ids is not None:
        tags = (await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))).scalars().all()
        article.tags = list(tags)

    # Set published_at only on first publish
    if article.status == ArticleStatus.published and not was_published and not article.published_at:
        article.published_at = datetime.now(timezone.utc)

    article.updated_at = datetime.now(timezone.utc)
    await db.commit()

    result = await db.execute(
        select(Article).options(*_load_options()).where(Article.id == article_id)
    )
    article = result.scalar_one()

    if article.status == ArticleStatus.published:
        await _trigger_revalidate(article.slug)

    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="找不到文章")
    await db.delete(article)
    await db.commit()
