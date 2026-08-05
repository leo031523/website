from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret, mask_secret
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.ai_settings import AIProvider, AIProviderSettings
from app.models.user import User
from app.schemas.ai_settings import (
    AIProviderSettingsCreate,
    AIProviderSettingsResponse,
    AIProviderSettingsUpdate,
)

router = APIRouter(prefix="/api/ai/settings", tags=["ai-settings"])


def _to_response(s: AIProviderSettings) -> AIProviderSettingsResponse:
    return AIProviderSettingsResponse(
        id=s.id,
        provider=s.provider,
        model=s.model,
        base_url=s.base_url,
        is_configured=s.encrypted_api_key is not None,
        api_key_suffix=None,  # 遮罩尾碼只在建立/更新當下短暫可得，見下方 _mask_cache
        is_enabled=s.is_enabled,
        timeout_seconds=s.timeout_seconds,
        max_output_tokens=s.max_output_tokens,
        top_k=s.top_k,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.get("", response_model=list[AIProviderSettingsResponse])
async def list_ai_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(AIProviderSettings).order_by(AIProviderSettings.id))
    return [_to_response(s) for s in result.scalars().all()]


@router.post("", response_model=AIProviderSettingsResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_settings(
    body: AIProviderSettingsCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    settings_row = AIProviderSettings(
        provider=body.provider,
        model=body.model,
        base_url=body.base_url,
        encrypted_api_key=encrypt_secret(body.api_key) if body.api_key else None,
        timeout_seconds=body.timeout_seconds,
        max_output_tokens=body.max_output_tokens,
        top_k=body.top_k,
    )
    db.add(settings_row)
    await db.commit()
    await db.refresh(settings_row)

    response = _to_response(settings_row)
    if body.api_key:
        response.api_key_suffix = mask_secret(body.api_key)
    return response


@router.put("/{settings_id}", response_model=AIProviderSettingsResponse)
async def update_ai_settings(
    settings_id: int,
    body: AIProviderSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.id == settings_id)
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        raise HTTPException(status_code=404, detail="找不到 AI provider 設定")

    if body.model is not None:
        settings_row.model = body.model
    if body.base_url is not None:
        settings_row.base_url = body.base_url
    if body.timeout_seconds is not None:
        settings_row.timeout_seconds = body.timeout_seconds
    if body.max_output_tokens is not None:
        settings_row.max_output_tokens = body.max_output_tokens
    if body.top_k is not None:
        settings_row.top_k = body.top_k

    new_key_suffix: str | None = None
    if body.remove_api_key:
        settings_row.encrypted_api_key = None
    elif body.api_key:
        settings_row.encrypted_api_key = encrypt_secret(body.api_key)
        new_key_suffix = mask_secret(body.api_key)

    await db.commit()
    await db.refresh(settings_row)

    response = _to_response(settings_row)
    response.api_key_suffix = new_key_suffix
    return response


@router.delete("/{settings_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_settings(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.id == settings_id)
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        raise HTTPException(status_code=404, detail="找不到 AI provider 設定")
    await db.delete(settings_row)
    await db.commit()


@router.post("/{settings_id}/enable", response_model=AIProviderSettingsResponse)
async def enable_ai_settings(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.id == settings_id)
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        raise HTTPException(status_code=404, detail="找不到 AI provider 設定")

    if not settings_row.encrypted_api_key:
        raise HTTPException(status_code=400, detail="尚未設定 API key，無法啟用")
    if not settings_row.model.strip():
        raise HTTPException(status_code=400, detail="尚未設定 model，無法啟用")
    if settings_row.provider == AIProvider.openai_compatible and not settings_row.base_url:
        raise HTTPException(status_code=400, detail="openai_compatible provider 必須設定 base_url")

    # 同一筆 transaction 內先停用所有 provider，再啟用目標 provider
    await db.execute(update(AIProviderSettings).values(is_enabled=False))
    settings_row.is_enabled = True
    await db.commit()
    await db.refresh(settings_row)
    return _to_response(settings_row)


@router.post("/{settings_id}/disable", response_model=AIProviderSettingsResponse)
async def disable_ai_settings(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.id == settings_id)
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        raise HTTPException(status_code=404, detail="找不到 AI provider 設定")
    settings_row.is_enabled = False
    await db.commit()
    await db.refresh(settings_row)
    return _to_response(settings_row)
