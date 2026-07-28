import re
import unicodedata
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models.project import Project, project_tags, project_tools
from app.models.tag import Tag
from app.models.tool import Tool
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _slugify(title: str) -> str:
    slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = slug.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-") or "project"


async def _unique_slug(slug: str, db: AsyncSession, exclude_id: int | None = None) -> str:
    base, counter = slug, 1
    while True:
        q = select(Project).where(Project.slug == slug)
        if exclude_id is not None:
            q = q.where(Project.id != exclude_id)
        if not (await db.execute(q)).scalar_one_or_none():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


async def _trigger_revalidate(slug: str) -> None:
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.frontend_url}/api/revalidate",
                json={"slug": slug, "secret": settings.revalidate_secret, "type": "project"},
                timeout=5.0,
            )
    except Exception:
        pass


def _load_options():
    return [
        selectinload(Project.tags),
        selectinload(Project.tools),
        selectinload(Project.cover_image),
    ]


@router.get("/id/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).options(*_load_options()).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="找不到專案")
    return project


@router.get("", response_model=list[ProjectListItem])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    stmt = (
        select(Project)
        .options(*_load_options())
        .order_by(Project.featured.desc(), Project.sort_order.asc(), Project.created_at.desc())
    )
    if current_user is None:
        stmt = stmt.where(Project.status == "published")
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    stmt = select(Project).options(*_load_options()).where(Project.slug == slug)
    if current_user is None:
        stmt = stmt.where(Project.status == "published")
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="找不到專案")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if body.slug:
        if (await db.execute(select(Project).where(Project.slug == body.slug))).scalar_one_or_none():
            raise HTTPException(status_code=400, detail="slug 已存在")
        slug = body.slug
    else:
        slug = await _unique_slug(_slugify(body.title), db)

    project = Project(
        title=body.title, slug=slug, summary=body.summary,
        content_md=body.content_md, tech_stack=body.tech_stack,
        repo_url=body.repo_url, demo_url=body.demo_url,
        status=body.status, featured=body.featured, sort_order=body.sort_order,
        cover_image_id=body.cover_image_id,
    )
    if body.status == "published":
        project.updated_at = datetime.now(timezone.utc)

    if body.tag_ids:
        project.tags = list((await db.execute(select(Tag).where(Tag.id.in_(body.tag_ids)))).scalars())
    if body.tool_ids:
        project.tools = list((await db.execute(select(Tool).where(Tool.id.in_(body.tool_ids)))).scalars())

    db.add(project)
    await db.commit()

    result = await db.execute(select(Project).options(*_load_options()).where(Project.id == project.id))
    project = result.scalar_one()

    if project.status == "published":
        await _trigger_revalidate(project.slug)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).options(*_load_options()).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="找不到專案")

    update_data = body.model_dump(exclude_none=True)
    tag_ids = update_data.pop("tag_ids", None)
    tool_ids = update_data.pop("tool_ids", None)

    if "slug" in update_data and update_data["slug"] != project.slug:
        if (await db.execute(
            select(Project).where(Project.slug == update_data["slug"], Project.id != project_id)
        )).scalar_one_or_none():
            raise HTTPException(status_code=400, detail="slug 已存在")

    for field, value in update_data.items():
        setattr(project, field, value)

    if tag_ids is not None:
        project.tags = list((await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))).scalars())
    if tool_ids is not None:
        project.tools = list((await db.execute(select(Tool).where(Tool.id.in_(tool_ids)))).scalars())

    project.updated_at = datetime.now(timezone.utc)
    await db.commit()

    result = await db.execute(select(Project).options(*_load_options()).where(Project.id == project_id))
    project = result.scalar_one()

    if project.status == "published":
        await _trigger_revalidate(project.slug)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="找不到專案")
    await db.delete(project)
    await db.commit()
