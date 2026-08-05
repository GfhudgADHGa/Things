"""Demonstrates, with actual constructed bytes, the real class of
vulnerability that this package's leaf/node hash domain separation
(hashing.py's 0x00 vs 0x01 prefixes) prevents: without it, a Merkle
tree's root can be exactly reproduced by a *structurally different*
tree -- different leaf count, different meaning -- because "hash of
some bytes" doesn't distinguish "these bytes are a leaf" from "these
bytes are the concatenation of two child hashes"."""
from __future__ import annotations

import hashlib

from merkle.hashing import leaf_hash, node_hash


def _naive_leaf_hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _naive_node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(left + right).digest()


def test_naive_undifferentiated_hashing_lets_a_1_leaf_tree_collide_with_a_2_leaf_tree():
    leaf_a = b"transaction A"
    leaf_b = b"transaction B"

    # the genuine two-leaf tree's root, using naive (non-domain-separated) hashing
    h_a = _naive_leaf_hash(leaf_a)
    h_b = _naive_leaf_hash(leaf_b)
    root_two_leaf_tree = _naive_node_hash(h_a, h_b)

    # a forged single-leaf "tree" whose one leaf is literally the two
    # child hashes concatenated -- under naive hashing this is *exactly*
    # the same SHA-256 call as computing the two-leaf root above
    forged_single_leaf = h_a + h_b
    root_forged_one_leaf_tree = _naive_leaf_hash(forged_single_leaf)

    assert root_two_leaf_tree == root_forged_one_leaf_tree
    # a verifier who only ever sees "the root is R" cannot tell these
    # two completely different datasets (2 real transactions vs. 1
    # forged 64-byte blob) apart under this naive scheme


def test_domain_separated_hashing_does_not_collide_on_the_identical_construction():
    leaf_a = b"transaction A"
    leaf_b = b"transaction B"

    h_a = leaf_hash(leaf_a)
    h_b = leaf_hash(leaf_b)
    root_two_leaf_tree = node_hash(h_a, h_b)

    forged_single_leaf = h_a + h_b
    root_forged_one_leaf_tree = leaf_hash(forged_single_leaf)

    # the 0x00 (leaf) vs 0x01 (node) prefix means these are now
    # different SHA-256 inputs, so the collision is gone
    assert root_two_leaf_tree != root_forged_one_leaf_tree


def test_domain_separation_holds_for_the_general_forgery_pattern():
    """Generalizes the single example above: for many different pairs
    of leaves, the naive scheme always reproduces the same collision
    (a structural certainty, not a coincidence of one input), and the
    domain-separated scheme never does."""
    import random

    rng = random.Random(1)
    for _ in range(200):
        leaf_a = bytes(rng.randrange(256) for _ in range(rng.randint(1, 16)))
        leaf_b = bytes(rng.randrange(256) for _ in range(rng.randint(1, 16)))

        naive_root = _naive_node_hash(_naive_leaf_hash(leaf_a), _naive_leaf_hash(leaf_b))
        naive_forged = _naive_leaf_hash(_naive_leaf_hash(leaf_a) + _naive_leaf_hash(leaf_b))
        assert naive_root == naive_forged

        real_root = node_hash(leaf_hash(leaf_a), leaf_hash(leaf_b))
        real_forged = leaf_hash(leaf_hash(leaf_a) + leaf_hash(leaf_b))
        assert real_root != real_forged
