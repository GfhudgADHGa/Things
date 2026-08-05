"""Fixed window counter: time is chopped into windows of `window_size`
seconds aligned to 0; each window allows up to `rate` requests, and the
counter resets hard the instant a new window begins.

Simple and cheap (one counter), but with a well-known flaw demonstrated
directly in test_fixed_window.py: a client that saves up its whole
budget for the end of one window and the start of the next can get
almost 2x `rate` requests through in a much shorter real time span than
window_size, straddling the boundary -- not a bug in this
implementation, an inherent property of resetting counts at fixed
boundaries instead of a truly sliding window.
"""
from __future__ import annotations

import math


class FixedWindowCounter:
    def __init__(self, rate: int, window_size: float):
        if rate <= 0 or window_size <= 0:
            raise ValueError("rate and window_size must be positive")
        self.rate = rate
        self.window_size = window_size
        self._window_index = None
        self._count = 0

    def allow(self, now: float) -> bool:
        window_index = math.floor(now / self.window_size)
        if window_index != self._window_index:
            self._window_index = window_index
            self._count = 0
        if self._count < self.rate:
            self._count += 1
            return True
        return False
