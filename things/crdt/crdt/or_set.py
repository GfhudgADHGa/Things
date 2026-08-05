"""An observed-remove set with add-wins semantics: adding an element
creates a fresh, globally-unique tag for that *specific add* (not just
for the element in general); removing an element tombstones exactly the
tags that were actually observed for it at removal time. An element is
present iff at least one of its add-tags isn't covered by a matching
tombstone.

"Add-wins" is the direct consequence of tagging each add individually: a
concurrent add and remove of the same element resolves to *present*,
because the remove can only tombstone tags it actually saw -- a
concurrent add (whose tag the remover never observed) necessarily
survives any merge. That's a real, deliberate design choice (a
"remove-wins" set is also a valid CRDT, just a different one) rather
than an accident of the implementation.
"""
from __future__ import annotations

from typing import Any, FrozenSet, Set, Tuple

Tag = Tuple[str, int]  # (replica_id, per-replica sequence number)


class ORSet:
    def __init__(self, replica_id: str):
        self.replica_id = replica_id
        self._counter = 0
        self.adds: Set[Tuple[Any, Tag]] = set()
        self.removes: Set[Tuple[Any, Tag]] = set()

    def _next_tag(self) -> Tag:
        self._counter += 1
        return (self.replica_id, self._counter)

    def add(self, element: Any) -> None:
        self.adds.add((element, self._next_tag()))

    def remove(self, element: Any) -> None:
        observed = {(e, tag) for e, tag in self.adds if e == element}
        self.removes |= observed

    def contains(self, element: Any) -> bool:
        return any(e == element and (e, tag) not in self.removes for e, tag in self.adds)

    def elements(self) -> Set[Any]:
        return {e for e, tag in self.adds if (e, tag) not in self.removes}

    def merge(self, other: "ORSet") -> "ORSet":
        result = ORSet(self.replica_id)
        result._counter = max(self._counter, other._counter)
        result.adds = self.adds | other.adds
        result.removes = self.removes | other.removes
        return result

    def state(self) -> Tuple[FrozenSet, FrozenSet]:
        return (frozenset(self.adds), frozenset(self.removes))
