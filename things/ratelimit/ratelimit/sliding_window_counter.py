"""Sliding window counter: approximates the sliding window log using
just two integer counters (current window, previous window) instead of
a full timestamp log, at the cost of assuming requests are spread
evenly within each window.

The estimate for "how many requests count toward the trailing window
ending at `now`" is:

    estimate = previous_window_count * overlap_fraction + current_window_count

where overlap_fraction is how much of the *previous* fixed window still
falls inside the trailing window of length window_size ending at now --
1.0 right at the start of the current window (the whole previous window
is still "behind" now), shrinking linearly to 0.0 by the end of it.
This is the same approximation used by several real-world rate limiters
(e.g. Cloudflare's published algorithm) specifically because it's O(1)
space regardless of `rate`.
"""
from __future__ import annotations

import math


class SlidingWindowCounter:
    def __init__(self, rate: int, window_size: float):
        if rate <= 0 or window_size <= 0:
            raise ValueError("rate and window_size must be positive")
        self.rate = rate
        self.window_size = window_size
        self._window_index = None
        self._current_count = 0
        self._previous_count = 0

    def allow(self, now: float) -> bool:
        window_index = math.floor(now / self.window_size)
        if self._window_index is None:
            self._window_index = window_index
        elif window_index != self._window_index:
            if window_index == self._window_index + 1:
                self._previous_count = self._current_count
            else:
                self._previous_count = 0
            self._current_count = 0
            self._window_index = window_index

        elapsed_in_window = now - window_index * self.window_size
        overlap_fraction = max(0.0, (self.window_size - elapsed_in_window) / self.window_size)
        estimate = self._previous_count * overlap_fraction + self._current_count

        if estimate < self.rate:
            self._current_count += 1
            return True
        return False
