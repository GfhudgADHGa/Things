"""An independently-coded reference implementation of ring routing --
no bisect, no maintained sorted list, just a fresh linear scan over
every virtual node position on every call. Slow, deliberately, and
useful only as a cross-check oracle in tests."""
from __future__ import annotations

from typing import Dict, List

from .hashing import ring_hash


def brute_force_get_node(key: str, physical_nodes: List[str], vnodes: int) -> str:
    if not physical_nodes:
        raise RuntimeError("no nodes")
    h = ring_hash(key)
    positions = []
    for node in physical_nodes:
        for i in range(vnodes):
            positions.append((ring_hash(f"{node}#{i}"), node))

    best = None
    for pos, node in positions:
        if pos >= h and (best is None or pos < best[0]):
            best = (pos, node)
    if best is None:
        # wrapped all the way around: the answer is whichever virtual
        # node has the smallest position on the entire ring
        best = min(positions, key=lambda p: p[0])
    return best[1]
