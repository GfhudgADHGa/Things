"""An increment/decrement counter, built from two GCounters: one tracks
total increments, the other tracks total decrements, and the visible
value is their difference. Each half inherits GCounter's merge-by-max
safety independently, so the pair does too -- a common CRDT-design
pattern (compose smaller CRDTs, get the composite's correctness for
free) rather than something that needs its own from-scratch proof.
"""
from __future__ import annotations

from typing import Tuple

from .g_counter import GCounter


class PNCounter:
    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.positive = GCounter(replica_id)
        self.negative = GCounter(replica_id)

    def increment(self, amount: int = 1) -> None:
        self.positive.increment(amount)

    def decrement(self, amount: int = 1) -> None:
        self.negative.increment(amount)

    def value(self) -> int:
        return self.positive.value() - self.negative.value()

    def merge(self, other: "PNCounter") -> "PNCounter":
        result = PNCounter(self.replica_id)
        result.positive = self.positive.merge(other.positive)
        result.negative = self.negative.merge(other.negative)
        return result

    def state(self) -> Tuple[dict, dict]:
        return (self.positive.state(), self.negative.state())
