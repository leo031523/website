from fastapi import Request


def client_key(request: Request) -> str:
    """依 X-Real-IP / X-Forwarded-For / 連線本身取得客戶端識別，用於
    per-IP 的速率限制。nginx 反向代理會設定 X-Real-IP；本機開發沒有
    反向代理時，直接用連線本身的 client host。"""
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
