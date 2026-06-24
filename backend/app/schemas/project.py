from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.tag import TagResponse
from app.schemas.tool import ToolResponse


class ProjectCreate(BaseModel):
    title: str
    slug: str | None = None
    summary: str | None = None
    content_md: str = ""
    tech_stack: list[str] = []
    repo_url: str | None = None
    demo_url: str | None = None
    status: Literal["draft", "published"] = "draft"
    featured: bool = False
    sort_order: int = 0
    tag_ids: list[int] = []
    tool_ids: list[int] = []
    cover_image_id: int | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    summary: str | None = None
    content_md: str | None = None
    tech_stack: list[str] | None = None
    repo_url: str | None = None
    demo_url: str | None = None
    status: Literal["draft", "published"] | None = None
    featured: bool | None = None
    sort_order: int | None = None
    tag_ids: list[int] | None = None
    tool_ids: list[int] | None = None
    cover_image_id: int | None = None


class ProjectListItem(BaseModel):
    id: int
    title: str
    slug: str
    summary: str | None
    tech_stack: list[str]
    repo_url: str | None
    demo_url: str | None
    status: str
    featured: bool
    sort_order: int
    cover_image_id: int | None
    tags: list[TagResponse]
    tools: list[ToolResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectResponse(ProjectListItem):
    content_md: str
