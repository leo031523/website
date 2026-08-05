import re
from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"http", "https"}
# RFC 3986: scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def normalize_external_url(value: str | None) -> str | None:
    """正規化並驗證使用者提供的外部連結。

    - 空字串視為未填寫，回傳 None。
    - 完全沒有 scheme 前綴的網址（例如 "github.com/x"）自動補上 https://。
    - 只要偵測到任何 scheme 前綴（例如 "javascript:"、"data:"），一律照該
      scheme 驗證，不會因為沒有 "://" 就誤判成裸網域而放行。
    - 僅允許 http/https，拒絕 javascript:、data: 等危險 scheme。
    """
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None

    if not _SCHEME_RE.match(trimmed):
        trimmed = f"https://{trimmed}"

    parsed = urlparse(trimmed)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError("URL 僅允許 http 或 https")
    if not parsed.netloc:
        raise ValueError("不是有效的網址")
    return trimmed
