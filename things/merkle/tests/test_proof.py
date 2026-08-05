import random

import pytest

from merkle.tree import MerkleTree, ProofStep, verify_proof


def _random_leaves(rng, n, size=8):
    return [bytes(rng.randrange(256) for _ in range(size)) for _ in range(n)]


@pytest.mark.parametrize("seed", range(200))
def test_every_leafs_proof_verifies_against_the_real_root(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 40)
    leaves = _random_leaves(rng, n)
    tree = MerkleTree(leaves)
    for i, leaf in enumerate(leaves):
        assert verify_proof(leaf, tree.proof(i), tree.root)


@pytest.mark.parametrize("seed", range(150))
def test_proof_rejects_a_different_leaf_value(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 30)
    leaves = _random_leaves(rng, n)
    tree = MerkleTree(leaves)
    i = rng.randrange(n)
    forged_leaf = bytes(rng.randrange(256) for _ in range(8))
    assert forged_leaf != leaves[i]
    assert not verify_proof(forged_leaf, tree.proof(i), tree.root)


@pytest.mark.parametrize("seed", range(150))
def test_proof_rejects_a_tampered_sibling_hash(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 30)
    leaves = _random_leaves(rng, n)
    tree = MerkleTree(leaves)
    i = rng.randrange(n)
    proof = tree.proof(i)
    assert any(step.sibling is not None for step in proof)  # guaranteed for n >= 2

    tampered = list(proof)
    step_idx = rng.choice([j for j, s in enumerate(proof) if s.sibling is not None])
    bad_sibling = bytearray(tampered[step_idx].sibling)
    bad_sibling[0] ^= 0xFF
    tampered[step_idx] = ProofStep(sibling=bytes(bad_sibling), sibling_is_left=tampered[step_idx].sibling_is_left)

    assert not verify_proof(leaves[i], tampered, tree.root)


@pytest.mark.parametrize("seed", range(100))
def test_proof_rejects_wrong_root(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 20)
    leaves = _random_leaves(rng, n)
    tree = MerkleTree(leaves)
    other_leaves = _random_leaves(rng, rng.randint(1, 20))
    other_root = MerkleTree(other_leaves).root
    if other_root == tree.root:
        return  # astronomically unlikely; skip rather than false-fail
    i = rng.randrange(n)
    assert not verify_proof(leaves[i], tree.proof(i), other_root)


def test_proof_index_out_of_range_raises():
    tree = MerkleTree([b"a", b"b", b"c"])
    with pytest.raises(IndexError):
        tree.proof(3)
    with pytest.raises(IndexError):
        tree.proof(-1)


def test_swapping_sibling_side_flag_breaks_verification():
    """The sibling_is_left flag isn't cosmetic -- swapping it changes
    the hash-order (node_hash(a, b) != node_hash(b, a) in general),
    so a proof with the correct sibling hash but the wrong side must
    still fail."""
    leaves = [f"leaf-{i}".encode() for i in range(4)]
    tree = MerkleTree(leaves)
    proof = tree.proof(0)
    assert proof[0].sibling is not None

    flipped = list(proof)
    flipped[0] = ProofStep(sibling=flipped[0].sibling, sibling_is_left=not flipped[0].sibling_is_left)
    assert not verify_proof(leaves[0], flipped, tree.root)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 15, 16, 17])
def test_proof_length_never_exceeds_number_of_tree_levels(n):
    leaves = [f"leaf-{i}".encode() for i in range(n)]
    tree = MerkleTree(leaves)
    max_possible_levels = n.bit_length() + 1
    for i in range(n):
        assert len(tree.proof(i)) <= max_possible_levels
