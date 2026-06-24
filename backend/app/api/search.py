from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.article import Article, ArticleStatus
from app.models.project import Project
from app.schemas.search import SearchResponse

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query("", min_length=1, max_length=200),
    db: AsyncSession = Depends(get_db),
):
    if not q.strip():
        return SearchResponse(query=q, articles=[], projects=[])

    pattern = f"%{q.strip()}%"

    articles_stmt = (
        select(Article)
        .options(selectinload(Article.category), selectinload(Article.tags))
        .where(
            Article.status == ArticleStatus.published,
            or_(
                Article.title.ilike(pattern),
                Article.excerpt.ilike(pattern),
                Article.content_md.ilike(pattern),
            ),
        )
        .order_by(Article.published_at.desc())
        .limit(10)
    )

    projects_stmt = (
        select(Project)
        .options(selectinload(Project.tags), selectinload(Project.tools))
        .where(
            Project.status == "published",
            or_(
                Project.title.ilike(pattern),
                Project.summary.ilike(pattern),
            ),
        )
        .limit(10)
    )

    articles = (await db.execute(articles_stmt)).scalars().all()
    projects = (await db.execute(projects_stmt)).scalars().all()

    return SearchResponse(query=q, articles=list(articles), projects=list(projects))
