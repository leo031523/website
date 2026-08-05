import json
import logging
import sys

# logging.LogRecord 內建屬性，格式化時要排除，只保留呼叫端透過
# extra={...} 額外附加的欄位（例如 request_id、slug、error_type）。
_RESERVED_LOG_RECORD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # uvicorn 自帶的 access log 交由我們自己的 request logging middleware 取代，
    # 避免同一個請求被記錄兩次、格式又不一致。
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False
    # httpx/httpcore 預設會在 INFO 等級記錄每個外送請求的完整 URL；
    # 若呼叫端把密鑰放在 query string（即使我們自己盡量避免），這行
    # log 就會外洩密鑰。調高等級到 WARNING，只保留連線層級的真正異常。
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
