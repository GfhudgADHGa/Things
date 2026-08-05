"""A last-writer-wins register: a single mutable value, resolved on
conflict by (timestamp, writer_id) -- the writer_id tiebreaker matters
for real correctness, not just tidiness: two replicas racing to write at
the exact same timestamp is a real possibility (clock resolution is
finite), and without a deterministic tiebreaker, "latest write wins"
stops being a well-defined total order, which breaks merge's
commutativity (two replicas could each think *their own* concurrent
write at the same timestamp is the winner).

A subtlety worth being explicit about: `writer_id` (who actually wrote
the currently-stored value) has to be tracked separately from
`replica_id` (which local instance this Python object is). An earlier
design collapsed the two -- merge() building its result as
`LWWRegister(self.replica_id, winner.value, winner.timestamp)` -- which
looks reasonable but silently discards *whose* write actually won
whenever `other`'s value wins the merge, corrupting the tiebreaker for
every merge after that one. Kept them separate from the start once that
became clear while designing this, rather than shipping it and finding
out via a failing associativity test (see test_lww_register.py, which
checks exactly the scenario -- a three-way merge where the winning
value originated from the "middle" replica -- that would have caught it).
"""
from __future__ import annotations

from typing import Any, Tuple


class LWWRegister:
    def __init__(self, replica_id: str, value: Any = None, timestamp: float = 0.0, writer_id: str = None):
        self.replica_id = replica_id
        self.value = value
        self.timestamp = timestamp
        self.writer_id = writer_id if writer_id is not None else replica_id

    def set(self, value: Any, timestamp: float) -> None:
        candidate_key = (timestamp, self.replica_id)
        current_key = (self.timestamp, self.writer_id)
        if candidate_key >= current_key:
            self.value = value
            self.timestamp = timestamp
            self.writer_id = self.replica_id

    def merge(self, other: "LWWRegister") -> "LWWRegister":
        self_key = (self.timestamp, self.writer_id)
        other_key = (other.timestamp, other.writer_id)
        winner = self if self_key >= other_key else other
        return LWWRegister(self.replica_id, winner.value, winner.timestamp, winner.writer_id)

    def state(self) -> Tuple[Any, float, str]:
        return (self.value, self.timestamp, self.writer_id)
