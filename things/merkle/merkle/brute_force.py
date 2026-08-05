"""An independently-coded root computation -- recursive rather than
the tree's iterative level-by-level construction, with its own fresh
indexing logic -- used only as a cross-check oracle in tests, so a
coding mistake in tree.py's level-building loop is unlikely to be
replicated here by coincidence."""
from __future__ import annotations

from typing import List, Sequence

from .hashing import leaf_hash, node_hash


def brute_force_root(leaves: Sequence[bytes]) -> bytes:
    if not leaves:
        raise ValueError("cannot build a Merkle tree with zero leaves")
    return _reduce([leaf_hash(leaf) for leaf in leaves])


def _reduce(level: List[bytes]) -> bytes:
    if len(level) == 1:
        return level[0]
    paired = []
    for i in range(0, len(level), 2):
        if i + 1 < len(level):
            paired.append(node_hash(level[i], level[i + 1]))
        else:
            paired.append(level[i])
    return _reduce(paired)
