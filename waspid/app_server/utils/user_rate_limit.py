"""Per-user sliding-window rate limiter for expensive endpoints.

Complements the global per-IP ``RateLimitMiddleware``: that protects
against flooding, this caps costly operations (LLM generation, outbound
tool execution) per authenticated user. In-memory and per-process —
multi-replica deployments should also enforce limits at the gateway.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class UserRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, user_id: str | None, now: float | None = None) -> bool:
        key = user_id or '__anonymous__'
        now = now if now is not None else time.monotonic()
        window = self._history[key]
        cutoff = now - self.window_seconds
        while window and window[0] <= cutoff:
            window.popleft()
        if len(window) >= self.max_requests:
            return False
        window.append(now)
        return True
