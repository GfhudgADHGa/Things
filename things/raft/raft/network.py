"""A network fault-injection policy: decides whether a message between
two nodes is delivered at all (dropped, or blocked by a partition) and,
if so, after how much simulated delay. This is deliberately just a
policy object with no clock or queue of its own -- cluster.py owns the
actual event scheduling, so the same policy logic is easy to unit-test
in isolation (see tests/test_network.py) and easy to reason about
separately from Raft's own state machine.
"""
from __future__ import annotations

import random
from typing import Dict, Optional, Sequence


class Network:
    def __init__(
        self,
        rng: random.Random,
        min_delay: int = 1,
        max_delay: int = 5,
        drop_probability: float = 0.0,
    ):
        self.rng = rng
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.drop_probability = drop_probability
        self._group_of: Optional[Dict[int, int]] = None  # None means fully connected

    def partition(self, groups: Sequence[Sequence[int]]) -> None:
        """Splits the network into isolated groups: nodes in different
        groups can no longer exchange messages in either direction until
        heal() is called."""
        group_of = {}
        for group_index, group in enumerate(groups):
            for node_id in group:
                group_of[node_id] = group_index
        self._group_of = group_of

    def heal(self) -> None:
        self._group_of = None

    def connected(self, a: int, b: int) -> bool:
        if self._group_of is None:
            return True
        return self._group_of.get(a) == self._group_of.get(b)

    def transmit_delay_or_none(self, sender: int, receiver: int) -> Optional[int]:
        """None means "drop this message" (partitioned apart, or random
        loss); otherwise the simulated delay in ticks before delivery."""
        if not self.connected(sender, receiver):
            return None
        if self.rng.random() < self.drop_probability:
            return None
        return self.rng.randint(self.min_delay, self.max_delay)
