"""A Merkle tree: leaves are hashed, then hashed together in pairs
level by level up to a single root hash. Any change to any leaf, at
any position, changes every hash on the path up to the root -- which
is the entire point: a single short root hash commits to the exact
contents of every leaf, and a small "proof" (the sibling hashes along
one leaf's path to the root) lets anyone verify a specific leaf is
part of the committed set without seeing the rest of it.

Odd node counts at a level are handled by promoting the leftover node
*unchanged* to the next level, rather than duplicating it. Duplicating
is a common alternative (and what early Bitcoin did) but it introduces
its own real, documented weakness (CVE-2012-2459): two different lists
of leaves -- one a genuine even-length list, one an odd-length list
whose last leaf equals its own duplicate -- can be made to produce the
same root, letting an attacker's forged list masquerade as the
original. Promoting unchanged avoids that whole failure class, at the
cost of a proof step that sometimes has "no sibling" instead.
"""
from __future__ import annotations

from typing import List, NamedTuple, Optional, Sequence

from .hashing import leaf_hash, node_hash


class ProofStep(NamedTuple):
    sibling: Optional[bytes]  # None means "promoted unchanged, no sibling"
    sibling_is_left: bool     # meaningless when sibling is None


def _build_levels(leaves: Sequence[bytes]) -> List[List[bytes]]:
    if not leaves:
        raise ValueError("cannot build a Merkle tree with zero leaves")
    levels = [[leaf_hash(leaf) for leaf in leaves]]
    while len(levels[-1]) > 1:
        current = levels[-1]
        next_level = []
        i = 0
        while i < len(current):
            if i + 1 < len(current):
                next_level.append(node_hash(current[i], current[i + 1]))
            else:
                next_level.append(current[i])  # odd one out: promote unchanged
            i += 2
        levels.append(next_level)
    return levels


class MerkleTree:
    def __init__(self, leaves: Sequence[bytes]):
        self.leaves = list(leaves)
        self._levels = _build_levels(self.leaves)

    @property
    def root(self) -> bytes:
        return self._levels[-1][0]

    def proof(self, index: int) -> List[ProofStep]:
        if not 0 <= index < len(self.leaves):
            raise IndexError(f"leaf index {index} out of range")
        steps: List[ProofStep] = []
        idx = index
        for level in self._levels[:-1]:
            if idx % 2 == 0:
                if idx + 1 < len(level):
                    steps.append(ProofStep(sibling=level[idx + 1], sibling_is_left=False))
                else:
                    steps.append(ProofStep(sibling=None, sibling_is_left=False))
            else:
                steps.append(ProofStep(sibling=level[idx - 1], sibling_is_left=True))
            idx //= 2
        return steps


def verify_proof(leaf: bytes, proof: Sequence[ProofStep], root: bytes) -> bool:
    """Verifies a leaf's membership using nothing but the leaf, its
    proof, and the root -- no tree object required, matching how a
    real verifier (who only ever received the root, not the whole
    dataset) would check it."""
    current = leaf_hash(leaf)
    for step in proof:
        if step.sibling is None:
            continue
        if step.sibling_is_left:
            current = node_hash(step.sibling, current)
        else:
            current = node_hash(current, step.sibling)
    return current == root
