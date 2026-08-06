import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionError, decrypt_secret, encrypt_secret, mask_secret
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.ai_settings import AIProvider, AIProviderSettings
from app.models.user import User
from app.schemas.ai_settings import (
    AIProviderSettingsCreate,
    AIProviderSettingsResponse,
    AIProviderSettingsUpdate,
    AITestConnectionResponse,
)
from app.services.ai.base import ChatMessage, ProviderError
from app.services.ai.registry import SUPPORTED_PROVIDERS, get_adapter

router = APIRouter(prefix="/api/ai/settings", tags=["ai-settings"])
logger = logging.getLogger("app.ai")

_TEST_COOLDOWN_SECONDS = 5.0
_TEST_MAX_OUTPUT_TOKENS = 16
_TEST_TIMEOUT_SECONDS = 10.0
_TEST_SYSTEM_PROMPT = "這是連線測試，請只回覆「ok」兩個字，不要說明任何其他內容。"
_TEST_MESSAGE = "ping"

# in-process 節流：避免後台重複點擊測試連線按鈕造成不必要的 provider 費用。
# 單一 process、單一管理者的個人網站規模，不需要額外引入 Redis 之類的共用儲存。
_last_test_at: dict[int, float] = {}


def _mask_current_key(s: AIProviderSettings) -> str | None:
    """讀取設定時也回傳遮罩後的尾碼（例如 ****ab12），不是只有建立／更新
    當下才看得到——管理者事後回來查看時，才能確認目前生效的是哪把 key。
    解密只是為了算出遮罩尾碼，這個函式本身絕不回傳完整明文。"""
    if not s.encrypted_api_key:
        return None
    try:
        return mask_secret(decrypt_secret(s.encrypted_api_key))
    except DecryptionError:
        return None


def _to_response(s: AIProviderSettings) -> AIProviderSettingsResponse:
    return AIProviderSettingsResponse(
        id=s.id,
        provider=s.provider,
        model=s.model,
        base_url=s.base_url,
        is_configured=s.encrypted_api_key is not None,
        api_key_suffix=_mask_current_key(s),
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
    return _to_response(settings_row)


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

    if body.remove_api_key:
        settings_row.encrypted_api_key = None
    elif body.api_key:
        settings_row.encrypted_api_key = encrypt_secret(body.api_key)

    await db.commit()
    await db.refresh(settings_row)
    return _to_response(settings_row)


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

    if settings_row.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="此 provider 尚未支援，暫時只能啟用 Gemini")
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


@router.post("/{settings_id}/test", response_model=AITestConnectionResponse)
async def test_ai_connection(
    settings_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """用最小 token 與固定測試訊息驗證 provider 連線是否正常。

    只回傳 provider、model、延遲與安全化後的錯誤分類；絕不回傳
    原始 request header、API key 或 provider 的完整 response。
    """
    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.id == settings_id)
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row:
        raise HTTPException(status_code=404, detail="找不到 AI provider 設定")
    if not settings_row.encrypted_api_key:
        raise HTTPException(status_code=400, detail="尚未設定 API key")
    if settings_row.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="此 provider 尚未支援，暫時只能測試 Gemini")

    now = time.monotonic()
    last = _last_test_at.get(settings_id)
    if last is not None and (now - last) < _TEST_COOLDOWN_SECONDS:
        wait = _TEST_COOLDOWN_SECONDS - (now - last)
        raise HTTPException(status_code=429, detail=f"請等待 {wait:.0f} 秒後再測試連線")
    _last_test_at[settings_id] = now

    api_key = decrypt_secret(settings_row.encrypted_api_key)
    adapter = get_adapter(settings_row.provider)

    try:
        result = await adapter.chat(
            api_key=api_key,
            model=settings_row.model,
            system_prompt=_TEST_SYSTEM_PROMPT,
            messages=[ChatMessage(role="user", content=_TEST_MESSAGE)],
            timeout_seconds=min(settings_row.timeout_seconds, _TEST_TIMEOUT_SECONDS),
            max_output_tokens=_TEST_MAX_OUTPUT_TOKENS,
            base_url=settings_row.base_url,
        )
    except ProviderError as exc:
        logger.warning(
            "ai connection test failed",
            extra={
                "settings_id": settings_id,
                "provider": settings_row.provider,
                "error_category": exc.category,
            },
        )
        return AITestConnectionResponse(
            provider=settings_row.provider,
            model=settings_row.model,
            success=False,
            error_category=exc.category,
        )

    logger.info(
        "ai connection test succeeded",
        extra={
            "settings_id": settings_id,
            "provider": settings_row.provider,
            "latency_ms": round(result.latency_ms, 1),
        },
    )
    return AITestConnectionResponse(
        provider=settings_row.provider,
        model=settings_row.model,
        success=True,
        latency_ms=round(result.latency_ms, 1),
    )
