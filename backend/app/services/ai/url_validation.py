import ipaddress
import socket
from urllib.parse import urlparse

from app.core.config import settings


class UnsafeProviderURLError(Exception):
    """base_url 指向不允許的目標（scheme 不對、loopback、內網、metadata IP
    等），用來擋 SSRF。只有 OpenAI-compatible provider 會用到——Gemini、
    OpenAI、Claude 一律用程式內定義的官方 endpoint，使用者輸入永遠不會
    變成實際打出去的 URL。"""


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_loopback
        or ip.is_link_local  # 涵蓋雲端 metadata IP，例如 169.254.169.254
        or ip.is_private
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _allowed_hosts() -> set[str]:
    return {h.strip().lower() for h in settings.ai_local_model_allowlist.split(",") if h.strip()}


def validate_provider_base_url(url: str) -> None:
    """驗證使用者設定的 OpenAI-compatible base_url 是否安全。

    scheme 檢查在任何環境都會執行；loopback／內網／metadata IP 的檢查
    只在 APP_ENV=production 時套用，本機開發預設允許連到自己電腦或
    Docker network 內的模型（例如 Ollama），不需要額外設定。
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise UnsafeProviderURLError(f"不允許的 URL scheme：{parsed.scheme or '(空白)'}")

    if not parsed.hostname:
        raise UnsafeProviderURLError("URL 缺少主機名稱")

    if settings.app_env != "production":
        return

    if parsed.hostname.lower() in _allowed_hosts():
        return

    try:
        addr_infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeProviderURLError(f"無法解析主機名稱：{parsed.hostname}") from exc

    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if _is_blocked_ip(ip):
            raise UnsafeProviderURLError(
                f"正式環境不允許連線到內網／loopback／metadata 位址：{ip}"
                "；若確實需要連線到內網的自架模型，"
                "請把主機名稱加入 AI_LOCAL_MODEL_ALLOWLIST。"
            )
