"""Naive hash(key) % len(nodes) routing, for contrast with the ring.
Simple and perfectly uniform for a *fixed* node list, but changing the
node count changes the modulus, which reshuffles nearly every key --
exactly the problem consistent hashing exists to avoid."""
from __future__ import annotations

from typing import List

from .hashing import ring_hash


def naive_route(key: str, nodes: List[str]) -> str:
    if not nodes:
        raise RuntimeError("no nodes")
    idx = ring_hash(key) % len(nodes)
    return nodes[idx]
