import uuid

from app.services.ai.rate_limit import check_rate_limit, reset_rate_limit


def _unique_key() -> str:
    return f"test-client-{uuid.uuid4().hex[:12]}"


def test_allows_requests_under_the_limit():
    key = _unique_key()
    try:
        for _ in range(10):
            allowed, message = check_rate_limit(key)
            assert allowed is True
            assert message is None
    finally:
        reset_rate_limit(key)


def test_blocks_requests_over_the_per_minute_limit():
    key = _unique_key()
    try:
        for _ in range(10):
            allowed, _ = check_rate_limit(key)
            assert allowed is True
        allowed, message = check_rate_limit(key)
        assert allowed is False
        assert message is not None
    finally:
        reset_rate_limit(key)


def test_different_clients_have_independent_limits():
    key_a = _unique_key()
    key_b = _unique_key()
    try:
        for _ in range(10):
            assert check_rate_limit(key_a)[0] is True
        assert check_rate_limit(key_a)[0] is False
        # 另一個 client 完全不受影響
        assert check_rate_limit(key_b)[0] is True
    finally:
        reset_rate_limit(key_a)
        reset_rate_limit(key_b)


def test_reset_clears_state():
    key = _unique_key()
    for _ in range(10):
        check_rate_limit(key)
    assert check_rate_limit(key)[0] is False
    reset_rate_limit(key)
    assert check_rate_limit(key)[0] is True
    reset_rate_limit(key)
