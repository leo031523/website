import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.about_content import AboutContent
from app.models.user import User
from app.schemas.about_content import AboutContentResponse, AboutContentUpdate

router = APIRouter(prefix="/api/about", tags=["about"])
logger = logging.getLogger("app.revalidate")


async def _trigger_revalidate() -> None:
    """觸發前端 ISR revalidate；失敗不應影響儲存本身是否成功，
    但失敗原因必須記錄下來，而不是靜默吞掉。"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.frontend_url}/api/revalidate",
                json={"slug": "about", "secret": settings.revalidate_secret, "type": "about"},
                timeout=5.0,
            )
            response.raise_for_status()
    except Exception as exc:
        logger.warning(
            "ISR revalidation failed",
            extra={"content_type": "about", "slug": "about", "error_type": type(exc).__name__},
        )


@router.get("", response_model=AboutContentResponse)
async def get_about(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AboutContent).where(AboutContent.id == AboutContent.SINGLETON_ID))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="尚未設定關於我內容")
    return content


@router.put("", response_model=AboutContentResponse)
async def update_about(
    body: AboutContentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(AboutContent).where(AboutContent.id == AboutContent.SINGLETON_ID))
    content = result.scalar_one_or_none()
    if not content:
        content = AboutContent(id=AboutContent.SINGLETON_ID, content_md=body.content_md)
        db.add(content)
    else:
        content.content_md = body.content_md

    await db.commit()
    await db.refresh(content)
    await _trigger_revalidate()
    return content
