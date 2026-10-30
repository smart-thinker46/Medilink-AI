"""Small dependency-free per-user limiter for the local gateway."""
from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = max(1, per_minute)
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now, cutoff = time.monotonic(), time.monotonic() - 60
        bucket = self.events[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.per_minute:
            return False
        bucket.append(now)
        return True
