import time
from collections import defaultdict, deque

# 個人網站單一 process 規模，記憶體內的滑動視窗就夠用，不需要 Redis
# 之類的共用儲存（多個 worker/多台機器才需要，這裡沒有）。
_PER_MINUTE_LIMIT = 10
_PER_DAY_LIMIT = 100
_MINUTE_SECONDS = 60
_DAY_SECONDS = 86400

_minute_windows: dict[str, deque] = defaultdict(deque)
_day_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(client_key: str) -> tuple[bool, str | None]:
    """回傳 (是否允許, 若被擋下的說明)。允許時會記錄這次請求的時間戳，
    後續呼叫據此判斷是否超過每分鐘/每日上限。"""
    now = time.time()

    minute_q = _minute_windows[client_key]
    while minute_q and now - minute_q[0] > _MINUTE_SECONDS:
        minute_q.popleft()
    if len(minute_q) >= _PER_MINUTE_LIMIT:
        return False, "請求過於頻繁，請稍後再試"

    day_q = _day_windows[client_key]
    while day_q and now - day_q[0] > _DAY_SECONDS:
        day_q.popleft()
    if len(day_q) >= _PER_DAY_LIMIT:
        return False, "今日請求次數已達上限，請明天再試"

    minute_q.append(now)
    day_q.append(now)
    return True, None


def reset_rate_limit(client_key: str) -> None:
    """測試用：清除某個 client_key 的計數，避免測試之間互相干擾。"""
    _minute_windows.pop(client_key, None)
    _day_windows.pop(client_key, None)
