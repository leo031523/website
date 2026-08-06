import time
from collections import defaultdict, deque

_MINUTE_SECONDS = 60
_DAY_SECONDS = 86400


class SlidingWindowRateLimiter:
    """個人網站單一 process 規模，記憶體內的滑動視窗就夠用，不需要
    Redis 之類的共用儲存（多個 worker/多台機器才需要，這裡沒有）。

    每個呼叫端各自建立一個實例、各自設定限制，彼此的計數互不影響
    （例如 AI 聊天 API 跟登入端點用不同的額度）。
    """

    def __init__(self, per_minute: int, per_day: int):
        self._per_minute = per_minute
        self._per_day = per_day
        self._minute_windows: dict[str, deque] = defaultdict(deque)
        self._day_windows: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, str | None]:
        """回傳 (是否允許, 若被擋下的說明)。允許時會記錄這次請求的時間戳，
        後續呼叫據此判斷是否超過每分鐘/每日上限。"""
        now = time.time()

        minute_q = self._minute_windows[key]
        while minute_q and now - minute_q[0] > _MINUTE_SECONDS:
            minute_q.popleft()
        if len(minute_q) >= self._per_minute:
            return False, "請求過於頻繁，請稍後再試"

        day_q = self._day_windows[key]
        while day_q and now - day_q[0] > _DAY_SECONDS:
            day_q.popleft()
        if len(day_q) >= self._per_day:
            return False, "今日請求次數已達上限，請明天再試"

        minute_q.append(now)
        day_q.append(now)
        return True, None

    def reset(self, key: str) -> None:
        """測試用：清除某個 key 的計數，避免測試之間互相干擾。"""
        self._minute_windows.pop(key, None)
        self._day_windows.pop(key, None)
