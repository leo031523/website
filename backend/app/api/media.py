import io
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image, ImageSequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.media import Media
from app.models.user import User
from app.schemas.media import MediaResponse, MediaUpdate

router = APIRouter(prefix="/api/media", tags=["media"])

MEDIA_DIR = settings.media_dir
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PIXELS = 40_000_000  # 約 40 百萬像素上限，避免 decompression bomb

_FORMAT_INFO = {
    "JPEG": (".jpg", "image/jpeg"),
    "PNG": (".png", "image/png"),
    "GIF": (".gif", "image/gif"),
    "WEBP": (".webp", "image/webp"),
}


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


async def _read_upload(file: UploadFile) -> bytes:
    """以固定大小的區塊讀取上傳內容，超過上限立即中止，
    避免不受信任的檔案大小/Content-Length 造成記憶體耗盡。"""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_SIZE:
            raise HTTPException(status_code=400, detail="檔案超過 10 MB 限制")
        chunks.append(chunk)
    return b"".join(chunks)


def _reencode_image(contents: bytes) -> tuple[bytes, str, str]:
    """驗證並重新編碼圖片，不信任用戶端提供的 Content-Type 或副檔名。

    回傳 (重新編碼後的 bytes, 副檔名, mime_type)。任何格式不符、
    損毀、偽造或超過像素上限的檔案都會拋出 HTTPException(400)。
    """
    try:
        probe = Image.open(io.BytesIO(contents))
        probe.verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="檔案不是有效的圖片") from exc

    try:
        image = Image.open(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="檔案不是有效的圖片") from exc

    fmt = image.format
    if fmt not in _FORMAT_INFO:
        raise HTTPException(status_code=400, detail=f"不支援的圖片格式：{fmt}")

    width, height = image.size
    if width * height > MAX_PIXELS:
        raise HTTPException(status_code=400, detail="圖片尺寸超過上限")

    try:
        image.load()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="檔案不是有效的圖片") from exc

    ext, mime_type = _FORMAT_INFO[fmt]
    buffer = io.BytesIO()

    try:
        if fmt == "GIF":
            frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(image)]
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                loop=image.info.get("loop", 0),
                duration=image.info.get("duration", 100),
            )
        elif fmt == "JPEG":
            image.convert("RGB").save(buffer, format="JPEG", quality=90)
        else:  # PNG, WEBP
            img = image if image.mode in ("RGB", "RGBA") else image.convert("RGBA")
            img.save(buffer, format=fmt, quality=90 if fmt == "WEBP" else None)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="圖片重新編碼失敗") from exc

    return buffer.getvalue(), ext, mime_type


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
    contents = await _read_upload(file)
    image_bytes, ext, mime_type = _reencode_image(contents)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(MEDIA_DIR, unique_name)

    os.makedirs(MEDIA_DIR, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(image_bytes)

    media = Media(
        filename=unique_name,
        path=dest,
        mime_type=mime_type,
        size=len(image_bytes),
    )
    db.add(media)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        if os.path.exists(dest):
            os.remove(dest)
        raise
    await db.refresh(media)
    return _to_response(media)


@router.patch("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    body: MediaUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="找不到媒體")
    media.alt_text = body.alt_text
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
