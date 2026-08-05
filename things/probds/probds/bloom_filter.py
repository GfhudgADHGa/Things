"""A classic Bloom filter: an m-bit array and k hash functions. Adding
an item sets k bits; testing membership checks whether all k of an
item's bits are set. False negatives are structurally impossible (a
real member's bits are always set by its own insertion); false
positives happen when other items' insertions happen to have already
set all k of some absent item's bits.

Optimal sizing for a target false-positive rate p and n expected items
(standard formulas, derived by minimizing the false-positive-rate
expression over m and k):
    m = -n * ln(p) / (ln 2)^2
    k = (m / n) * ln 2
"""
from __future__ import annotations

import math

from .hashing import kth_hash


class BloomFilter:
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        if expected_items <= 0:
            raise ValueError("expected_items must be positive")
        if not 0 < false_positive_rate < 1:
            raise ValueError("false_positive_rate must be in (0, 1)")
        self.expected_items = expected_items
        self.target_fpr = false_positive_rate
        self.m = max(8, math.ceil(-expected_items * math.log(false_positive_rate) / (math.log(2) ** 2)))
        self.k = max(1, round((self.m / expected_items) * math.log(2)))
        self.bits = bytearray((self.m + 7) // 8)
        self.n_added = 0

    def _set_bit(self, idx: int) -> None:
        self.bits[idx // 8] |= 1 << (idx % 8)

    def _get_bit(self, idx: int) -> bool:
        return bool(self.bits[idx // 8] & (1 << (idx % 8)))

    def add(self, item) -> None:
        for i in range(self.k):
            self._set_bit(kth_hash(item, i, self.m))
        self.n_added += 1

    def __contains__(self, item) -> bool:
        return all(self._get_bit(kth_hash(item, i, self.m)) for i in range(self.k))

    def bits_set_fraction(self) -> float:
        count = sum(bin(byte).count("1") for byte in self.bits)
        return count / self.m

    def predicted_false_positive_rate(self) -> float:
        """The false-positive probability implied by the *actual* current
        bit-array fill ratio (not the a-priori target) -- (fraction of
        bits set)^k, since a false positive requires all k of a fresh
        item's independently-hashed bit positions to already be set."""
        return self.bits_set_fraction() ** self.k
