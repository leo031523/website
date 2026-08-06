from app.core.rate_limit import SlidingWindowRateLimiter

_PER_MINUTE_LIMIT = 10
_PER_DAY_LIMIT = 100

_limiter = SlidingWindowRateLimiter(per_minute=_PER_MINUTE_LIMIT, per_day=_PER_DAY_LIMIT)


def check_rate_limit(client_key: str) -> tuple[bool, str | None]:
    return _limiter.check(client_key)


def reset_rate_limit(client_key: str) -> None:
    """測試用：清除某個 client_key 的計數，避免測試之間互相干擾。"""
    _limiter.reset(client_key)
