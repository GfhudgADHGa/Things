"""Consistent hashing with virtual nodes.

Each physical node is represented by many "virtual node" positions on a
64-bit hash ring (hash(f"{node}#{i}") for i in range(vnodes)). A key is
routed to whichever virtual node position is the first one at or after
the key's own hash position, walking clockwise (wrapping around past
the largest position back to the smallest) -- so each physical node
owns the ring *arc* immediately preceding its virtual node positions.

This gives consistent hashing's headline property: adding or removing
one physical node only reassigns the keys that fell in *that* node's
arcs, not a global reshuffle -- unlike naive `hash(key) % len(nodes)`,
where changing the node count changes almost every key's `% len(nodes)`
result. Many virtual nodes per physical node also smooths out load
imbalance that a single ring position per node would otherwise leave to
chance.
"""
from __future__ import annotations

import bisect
from typing import Dict, List, Set

from .hashing import ring_hash


class ConsistentHashRing:
    def __init__(self, virtual_nodes_per_physical: int = 100):
        if virtual_nodes_per_physical < 1:
            raise ValueError("virtual_nodes_per_physical must be positive")
        self.vnodes = virtual_nodes_per_physical
        self._ring_keys: List[int] = []
        self._ring_map: Dict[int, str] = {}
        self._physical_nodes: Set[str] = set()

    def add_node(self, node: str) -> None:
        if node in self._physical_nodes:
            raise ValueError(f"node {node!r} already present")
        self._physical_nodes.add(node)
        for i in range(self.vnodes):
            h = ring_hash(f"{node}#{i}")
            self._ring_map[h] = node
            bisect.insort(self._ring_keys, h)

    def remove_node(self, node: str) -> None:
        if node not in self._physical_nodes:
            raise ValueError(f"node {node!r} not present")
        self._physical_nodes.discard(node)
        for i in range(self.vnodes):
            h = ring_hash(f"{node}#{i}")
            del self._ring_map[h]
            idx = bisect.bisect_left(self._ring_keys, h)
            del self._ring_keys[idx]

    def get_node(self, key: str) -> str:
        if not self._ring_keys:
            raise RuntimeError("ring is empty")
        h = ring_hash(key)
        idx = bisect.bisect_right(self._ring_keys, h) % len(self._ring_keys)
        return self._ring_map[self._ring_keys[idx]]

    def nodes(self) -> Set[str]:
        return set(self._physical_nodes)
