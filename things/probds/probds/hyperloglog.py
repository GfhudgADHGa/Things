"""HyperLogLog: estimates the number of *distinct* items added (the
cardinality) using O(2^b) memory regardless of how many items or
duplicates are added. Each item is hashed to 64 bits; the top b bits
pick one of m = 2^b registers, and the remaining (64 - b) bits determine
a "rank" (1 + the number of leading zero bits). Each register keeps the
maximum rank ever seen for its bucket -- intuitively, seeing a long run
of leading zeros among items hashed into a given bucket is unlikely
unless *many* distinct items landed there, so the maximum rank across a
bucket's history is evidence about how many distinct items hit it.
Combining all m registers via a (bias-corrected) harmonic mean gives the
classic Flajolet et al. estimator, with a standard error of
approximately 1.04/sqrt(m).
"""
from __future__ import annotations

import math
from typing import List

from .hashing import hash64


def _alpha(m: int) -> float:
    if m == 16:
        return 0.673
    if m == 32:
        return 0.697
    if m == 64:
        return 0.709
    return 0.7213 / (1 + 1.079 / m)


class HyperLogLog:
    def __init__(self, b: int = 10):
        if not 4 <= b <= 30:
            raise ValueError("b must be in [4, 30]")
        self.b = b
        self.m = 1 << b
        self.registers: List[int] = [0] * self.m
        self._value_bits = 64 - b

    def add(self, item) -> None:
        h = hash64(item)
        idx = h >> self._value_bits
        remaining = h & ((1 << self._value_bits) - 1)
        if remaining == 0:
            rank = self._value_bits + 1
        else:
            rank = self._value_bits - remaining.bit_length() + 1
        if rank > self.registers[idx]:
            self.registers[idx] = rank

    def estimate(self) -> float:
        m = self.m
        z = sum(2.0 ** (-r) for r in self.registers)
        raw = _alpha(m) * m * m / z
        if raw <= 2.5 * m:
            zeros = self.registers.count(0)
            if zeros > 0:
                return m * math.log(m / zeros)
        return raw

    @staticmethod
    def standard_error(m: int) -> float:
        return 1.04 / math.sqrt(m)
