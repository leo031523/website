from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.tool import Tool
from app.models.user import User
from app.schemas.tool import ToolCreate, ToolResponse, ToolUpdate

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("", response_model=list[ToolResponse])
async def list_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool).order_by(Tool.category, Tool.name))
    return result.scalars().all()


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    body: ToolCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tool = Tool(**body.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    body: ToolUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="找不到工具")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(tool, field, value)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="找不到工具")
    await db.delete(tool)
    await db.commit()
