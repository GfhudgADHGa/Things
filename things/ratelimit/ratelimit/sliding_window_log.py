"""Sliding window log: keeps the exact timestamp of every allowed
request in a deque, discarding any older than `window_size` seconds
behind `now` before deciding. This is the "exact" algorithm the other
three are all approximating or trading off against -- it enforces
"never more than `rate` requests in *any* trailing window of length
window_size" precisely, at the cost of remembering up to `rate`
timestamps per client instead of a couple of counters.
"""
from __future__ import annotations

from collections import deque


class SlidingWindowLog:
    def __init__(self, rate: int, window_size: float):
        if rate <= 0 or window_size <= 0:
            raise ValueError("rate and window_size must be positive")
        self.rate = rate
        self.window_size = window_size
        self.timestamps: deque = deque()

    def allow(self, now: float) -> bool:
        cutoff = now - self.window_size
        while self.timestamps and self.timestamps[0] <= cutoff:
            self.timestamps.popleft()
        if len(self.timestamps) < self.rate:
            self.timestamps.append(now)
            return True
        return False
