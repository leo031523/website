import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.media import Media
from app.models.user import User
from app.schemas.media import MediaResponse

router = APIRouter(prefix="/api/media", tags=["media"])

MEDIA_DIR = settings.media_dir
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _to_response(m: Media) -> MediaResponse:
    return MediaResponse(
        id=m.id,
        filename=m.filename,
        url=f"/uploads/{m.filename}",
        mime_type=m.mime_type,
        size=m.size,
        alt_text=m.alt_text,
        created_at=m.created_at,
    )


@router.get("", response_model=list[MediaResponse])
async def list_media(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Media).order_by(Media.created_at.desc()))
    return [_to_response(m) for m in result.scalars().all()]


@router.post("", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支援的檔案類型：{file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="檔案超過 10 MB 限制")

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(MEDIA_DIR, unique_name)

    os.makedirs(MEDIA_DIR, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(contents)

    media = Media(
        filename=unique_name,
        path=dest,
        mime_type=file.content_type or "application/octet-stream",
        size=len(contents),
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return _to_response(media)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="找不到媒體")

    if os.path.exists(media.path):
        os.remove(media.path)

    await db.delete(media)
    await db.commit()
