import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret
from app.core.database import get_db
from app.core.request_utils import client_key
from app.models.ai_settings import AIProviderSettings
from app.schemas.ai_chat import ChatRequest, ChatResponse, ChatStatusResponse
from app.services.ai.base import (
    ERROR_AUTH_FAILED,
    ERROR_RATE_LIMITED,
    ERROR_TIMEOUT,
    ERROR_UNAVAILABLE,
    ChatMessage,
    ProviderError,
)
from app.services.ai.prompt import (
    FALLBACK_ANSWER,
    build_system_prompt,
    extract_valid_sources,
    strip_citation_markers,
)
from app.services.ai.rate_limit import check_rate_limit
from app.services.ai.registry import get_adapter
from app.services.retrieval.retriever import retrieve

router = APIRouter(prefix="/api/ai", tags=["ai-chat"])
logger = logging.getLogger("app.ai")

_DEFAULT_TOP_K = 5
_MAX_REQUEST_BODY_BYTES = 20_000  # 遠大於 2000 字元 message + history 的合理上限

_PROVIDER_ERROR_STATUS: dict[str, tuple[int, str]] = {
    ERROR_AUTH_FAILED: (502, "AI 服務目前設定有誤，請聯絡網站管理者"),
    ERROR_TIMEOUT: (504, "AI 服務回應逾時，請稍後再試"),
    ERROR_UNAVAILABLE: (502, "AI 服務暫時無法使用，請稍後再試"),
    ERROR_RATE_LIMITED: (502, "AI 服務暫時繁忙，請稍後再試"),
}
_DEFAULT_PROVIDER_ERROR = (502, "AI 服務發生未知錯誤，請稍後再試")


async def _enforce_body_size_limit(request: Request) -> None:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > _MAX_REQUEST_BODY_BYTES:
        raise HTTPException(status_code=413, detail="請求內容過大")


def _error(status_code: int, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message, "request_id": request_id})


@router.get("/status", response_model=ChatStatusResponse)
async def status(db: AsyncSession = Depends(get_db)):
    """公開端點：AI 助理目前能不能用、是哪家 provider。前端用這個
    決定入口按鈕要不要顯示為可用狀態，不需要登入。"""
    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.is_enabled.is_(True))
    )
    settings_row = result.scalar_one_or_none()
    available = bool(settings_row and settings_row.encrypted_api_key)
    return ChatStatusResponse(
        available=available,
        provider=settings_row.provider if available and settings_row else None,
    )


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(_enforce_body_size_limit)])
async def chat(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    request_id = str(uuid.uuid4())

    allowed, limit_message = check_rate_limit(client_key(request))
    if not allowed:
        return _error(429, limit_message or "請求過於頻繁，請稍後再試", request_id)

    result = await db.execute(
        select(AIProviderSettings).where(AIProviderSettings.is_enabled.is_(True))
    )
    settings_row = result.scalar_one_or_none()
    if not settings_row or not settings_row.encrypted_api_key:
        return _error(503, "AI 助理目前尚未啟用，請稍後再試或聯絡網站管理者", request_id)

    chunks = await retrieve(db, body.message, top_k=settings_row.top_k or _DEFAULT_TOP_K)
    if not chunks:
        logger.info(
            "ai chat: no relevant content found",
            extra={"request_id": request_id, "provider": settings_row.provider},
        )
        return ChatResponse(
            answer=FALLBACK_ANSWER,
            sources=[],
            provider=settings_row.provider,
            model=settings_row.model,
            request_id=request_id,
            grounded=False,
        )

    system_prompt = build_system_prompt(chunks)
    adapter_messages = [ChatMessage(role=m.role, content=m.content) for m in body.history]
    adapter_messages.append(ChatMessage(role="user", content=body.message))

    api_key = decrypt_secret(settings_row.encrypted_api_key)
    try:
        adapter = get_adapter(settings_row.provider)
    except NotImplementedError:
        logger.error(
            "ai chat: enabled provider has no adapter implementation",
            extra={"request_id": request_id, "provider": settings_row.provider},
        )
        return _error(503, "AI 服務目前設定有誤，請聯絡網站管理者", request_id)

    start = time.monotonic()
    try:
        result_chat = await adapter.chat(
            api_key=api_key,
            model=settings_row.model,
            system_prompt=system_prompt,
            messages=adapter_messages,
            timeout_seconds=settings_row.timeout_seconds,
            max_output_tokens=settings_row.max_output_tokens,
            base_url=settings_row.base_url,
        )
    except ProviderError as exc:
        status_code, message = _PROVIDER_ERROR_STATUS.get(exc.category, _DEFAULT_PROVIDER_ERROR)
        logger.warning(
            "ai chat provider error",
            extra={
                "request_id": request_id,
                "provider": settings_row.provider,
                "error_category": exc.category,
            },
        )
        return _error(status_code, message, request_id)

    duration_ms = (time.monotonic() - start) * 1000
    sources = extract_valid_sources(result_chat.text, chunks)
    grounded = len(sources) > 0
    answer = strip_citation_markers(result_chat.text) if grounded else FALLBACK_ANSWER

    logger.info(
        "ai chat completed",
        extra={
            "request_id": request_id,
            "provider": settings_row.provider,
            "model": settings_row.model,
            "duration_ms": round(duration_ms, 1),
            "source_count": len(sources),
            "grounded": grounded,
        },
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        provider=settings_row.provider,
        model=settings_row.model,
        request_id=request_id,
        grounded=grounded,
    )
