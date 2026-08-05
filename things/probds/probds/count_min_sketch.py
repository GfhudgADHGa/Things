"""Count-Min Sketch: a d x w grid of counters. Adding an item with count
c increments one counter per row (row r's column chosen by an
independent hash of the item); estimating an item's count takes the
*minimum* across its d row-counters, since any given counter can only be
inflated by hash collisions with other items (never deflated), so the
minimum is the tightest available upper bound on the true count.

Standard sizing for additive error at most epsilon * (total count added)
with probability at least 1 - delta:
    w = ceil(e / epsilon)      (e = Euler's number)
    d = ceil(ln(1 / delta))

Rows MUST use genuinely independent hash functions, not variations on
a shared pair of base hashes -- see hashing.row_hash's docstring and
this package's README for a real bug this distinction caught.
"""
from __future__ import annotations

import math
from typing import List

from .hashing import row_hash


class CountMinSketch:
    def __init__(self, width: int, depth: int):
        if width < 1 or depth < 1:
            raise ValueError("width and depth must be positive")
        self.width = width
        self.depth = depth
        self.table: List[List[int]] = [[0] * width for _ in range(depth)]
        self.total = 0

    @staticmethod
    def for_error_bound(epsilon: float, delta: float) -> "CountMinSketch":
        width = math.ceil(math.e / epsilon)
        depth = math.ceil(math.log(1 / delta))
        return CountMinSketch(width, depth)

    def add(self, item, count: int = 1) -> None:
        for row in range(self.depth):
            col = row_hash(item, row, self.width)
            self.table[row][col] += count
        self.total += count

    def estimate(self, item) -> int:
        return min(self.table[row][row_hash(item, row, self.width)] for row in range(self.depth))
