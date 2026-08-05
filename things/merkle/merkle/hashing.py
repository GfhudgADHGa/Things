"""Domain-separated hashing for leaves vs. internal nodes.

Leaf hashes and internal-node hashes are computed with different
one-byte prefixes (0x00 vs 0x01) before being fed to SHA-256. This
isn't cosmetic -- see test_domain_separation.py for a constructed,
concrete demonstration of the real vulnerability this avoids: without
it, a two-leaf tree's root is indistinguishable from a *different*,
single-leaf tree whose one leaf happens to equal the two child hashes
concatenated, since both are then just "sha256 of some bytes" with
nothing to tell a leaf apart from an internal node. Early Bitcoin
didn't have this particular issue (it separates by tree *position*
differently), but the general class of leaf/node hash confusion is a
well-documented real weakness in naively-designed Merkle trees.
"""
from __future__ import annotations

import hashlib

_LEAF_PREFIX = b"\x00"
_NODE_PREFIX = b"\x01"


def leaf_hash(data: bytes) -> bytes:
    return hashlib.sha256(_LEAF_PREFIX + data).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(_NODE_PREFIX + left + right).digest()
