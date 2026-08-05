"""A grow-only counter: each replica tracks its own contribution
separately (keyed by replica_id), and the counter's value is the sum
across all replicas' contributions. merge() takes the element-wise
maximum of two replicas' per-replica counts -- since a single replica's
own count only ever increases, the max of two observations of that same
replica's count is always the more up-to-date one. That's the entire
mechanism that makes merge safe to apply in any order, any number of
times, with any duplicates: max is commutative, associative, and
idempotent, so a CRDT built entirely out of per-replica maxes inherits
all three properties for free (see test_g_counter.py, which checks
exactly those three laws, not just "the numbers come out right").
"""
from __future__ import annotations

from typing import Dict


class GCounter:
    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self.counts: Dict[str, int] = {}

    def increment(self, amount: int = 1) -> None:
        if amount < 0:
            raise ValueError("GCounter only ever increases; use PNCounter for decrements")
        self.counts[self.replica_id] = self.counts.get(self.replica_id, 0) + amount

    def value(self) -> int:
        return sum(self.counts.values())

    def merge(self, other: "GCounter") -> "GCounter":
        result = GCounter(self.replica_id)
        for replica_id in set(self.counts) | set(other.counts):
            result.counts[replica_id] = max(self.counts.get(replica_id, 0), other.counts.get(replica_id, 0))
        return result

    def state(self) -> Dict[str, int]:
        return dict(self.counts)
