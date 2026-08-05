import random

import pytest

from merkle.brute_force import brute_force_root
from merkle.hashing import leaf_hash
from merkle.tree import MerkleTree


def _random_leaves(rng, n, size=8):
    return [bytes(rng.randrange(256) for _ in range(size)) for _ in range(n)]


@pytest.mark.parametrize("seed", range(200))
def test_root_matches_brute_force_oracle(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 60)
    leaves = _random_leaves(rng, n)
    tree = MerkleTree(leaves)
    assert tree.root == brute_force_root(leaves)


@pytest.mark.parametrize("seed", range(150))
def test_flipping_any_single_leaf_byte_changes_the_root(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 30)
    leaves = _random_leaves(rng, n)
    original_root = MerkleTree(leaves).root

    victim = rng.randrange(n)
    byte_pos = rng.randrange(len(leaves[victim]))
    tampered = bytearray(leaves[victim])
    tampered[byte_pos] ^= 0xFF  # flip every bit of one byte
    leaves[victim] = bytes(tampered)

    new_root = MerkleTree(leaves).root
    assert new_root != original_root


@pytest.mark.parametrize("seed", range(50))
def test_deterministic_for_the_same_leaves(seed):
    rng = random.Random(seed)
    leaves = _random_leaves(rng, rng.randint(1, 20))
    assert MerkleTree(leaves).root == MerkleTree(list(leaves)).root


@pytest.mark.parametrize("seed", range(50))
def test_reordering_leaves_changes_the_root(seed):
    rng = random.Random(seed)
    n = rng.randint(4, 15)
    leaves = _random_leaves(rng, n)
    original = MerkleTree(leaves).root
    shuffled = list(leaves)
    while shuffled == leaves:
        rng.shuffle(shuffled)
    assert MerkleTree(shuffled).root != original


def test_single_leaf_tree_root_is_just_its_own_leaf_hash():
    leaf = b"only one leaf"
    tree = MerkleTree([leaf])
    assert tree.root == leaf_hash(leaf)
    assert tree.proof(0) == []


def test_empty_tree_raises():
    with pytest.raises(ValueError):
        MerkleTree([])


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 15, 16, 17, 31, 32, 33])
def test_various_leaf_counts_including_non_powers_of_two(n):
    leaves = [f"leaf-{i}".encode() for i in range(n)]
    tree = MerkleTree(leaves)
    assert tree.root == brute_force_root(leaves)
