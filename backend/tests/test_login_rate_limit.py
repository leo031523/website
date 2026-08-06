import app.api.auth as auth_module

_TEST_CLIENT_KEY = "testclient"


def test_login_blocks_after_per_minute_limit(client, admin_user):
    """防暴力破解：同一個來源在短時間內大量嘗試登入（不論帳密對不對），
    超過門檻後要被擋下，不能無限次猜密碼。"""
    auth_module._login_rate_limiter.reset(_TEST_CLIENT_KEY)
    try:
        for _ in range(5):
            res = client.post(
                "/api/auth/login",
                json={"username": admin_user["username"], "password": "wrong-password"},
            )
            assert res.status_code == 401

        res = client.post(
            "/api/auth/login",
            json={"username": admin_user["username"], "password": "wrong-password"},
        )
        assert res.status_code == 429
        assert "detail" in res.json()
    finally:
        auth_module._login_rate_limiter.reset(_TEST_CLIENT_KEY)


def test_login_rate_limit_also_counts_successful_attempts(client, admin_user):
    """限流是對「這個來源打了幾次」計數，不是只算失敗次數——不然攻擊者
    只要偶爾猜對一次（或對著一堆帳號亂猜）就能繞過限制。"""
    auth_module._login_rate_limiter.reset(_TEST_CLIENT_KEY)
    try:
        for _ in range(5):
            res = client.post(
                "/api/auth/login",
                json={"username": admin_user["username"], "password": admin_user["password"]},
            )
            assert res.status_code == 200

        res = client.post(
            "/api/auth/login",
            json={"username": admin_user["username"], "password": admin_user["password"]},
        )
        assert res.status_code == 429
    finally:
        auth_module._login_rate_limiter.reset(_TEST_CLIENT_KEY)


def test_login_rate_limit_is_independent_per_client(client, admin_user):
    auth_module._login_rate_limiter.reset(_TEST_CLIENT_KEY)
    auth_module._login_rate_limiter.reset("1.2.3.4")
    try:
        for _ in range(5):
            res = client.post(
                "/api/auth/login",
                json={"username": admin_user["username"], "password": "wrong-password"},
            )
            assert res.status_code == 401

        blocked = client.post(
            "/api/auth/login",
            json={"username": admin_user["username"], "password": "wrong-password"},
        )
        assert blocked.status_code == 429

        other_client_ok = client.post(
            "/api/auth/login",
            json={"username": admin_user["username"], "password": admin_user["password"]},
            headers={"X-Real-IP": "1.2.3.4"},
        )
        assert other_client_ok.status_code == 200
    finally:
        auth_module._login_rate_limiter.reset(_TEST_CLIENT_KEY)
        auth_module._login_rate_limiter.reset("1.2.3.4")
