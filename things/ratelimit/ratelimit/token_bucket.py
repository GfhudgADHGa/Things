"""Token bucket: tokens accumulate continuously at `rate` tokens/second,
capped at `capacity` (the maximum burst size). Each allowed request
spends one token; a request is denied if the bucket is empty.

Takes an explicit `now` on every call rather than reading a real clock,
so tests can simulate arbitrarily long traffic patterns instantly and
deterministically.
"""
from __future__ import annotations


class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be positive")
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = 0.0

    def allow(self, now: float) -> bool:
        if now < self.last_update:
            raise ValueError("time must not go backwards")
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False
