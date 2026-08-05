import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """記錄每個請求的 request_id、route、method、status 與耗時。

    不記錄 request/response body、headers（含 cookie）或 query string，
    避免密碼、JWT、API key 等敏感內容進入 log。
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            logger.error(
                "unhandled exception while processing request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": request.url.path,
                    "duration_ms": duration_ms,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "route": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
