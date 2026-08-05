import random

import pytest

from spellcheck.bk_tree import BKTree
from spellcheck.edit_distance import levenshtein
from spellcheck.words import COMMON_WORDS


def _brute_force_query(words, target, max_dist):
    return sorted(w for w in words if levenshtein(target, w) <= max_dist)


@pytest.mark.parametrize("seed", range(150))
def test_query_matches_brute_force_linear_scan(seed):
    """The whole point of a BK-tree is to avoid scanning every word --
    but it must still return *exactly* the same set a full linear scan
    would, since the triangle-inequality pruning only skips subtrees
    that are provably out of range, never a subtree that might contain
    a hit."""
    rng = random.Random(seed)
    sample = rng.sample(COMMON_WORDS, 250)
    tree = BKTree(levenshtein)
    for w in sample:
        tree.insert(w)

    target = rng.choice(COMMON_WORDS)
    max_dist = rng.choice([0, 1, 2, 3])

    got = sorted(tree.query(target, max_dist))
    expected = _brute_force_query(sample, target, max_dist)
    assert got == expected


def test_exact_match_is_always_included():
    tree = BKTree(levenshtein)
    for w in ["apple", "banana", "cherry"]:
        tree.insert(w)
    assert "apple" in tree.query("apple", 0)


def test_zero_distance_query_is_exact_membership_only():
    tree = BKTree(levenshtein)
    for w in ["cat", "cot", "cast"]:
        tree.insert(w)
    assert tree.query("cat", 0) == ["cat"]


def test_query_on_empty_tree_returns_empty():
    tree = BKTree(levenshtein)
    assert tree.query("anything", 5) == []


def test_duplicate_insert_does_not_grow_size():
    tree = BKTree(levenshtein)
    tree.insert("word")
    tree.insert("word")
    assert len(tree) == 1


@pytest.mark.parametrize("seed", range(50))
def test_larger_max_dist_returns_a_superset(seed):
    rng = random.Random(seed + 10_000)
    sample = rng.sample(COMMON_WORDS, 200)
    tree = BKTree(levenshtein)
    for w in sample:
        tree.insert(w)
    target = rng.choice(COMMON_WORDS)

    small = set(tree.query(target, 1))
    large = set(tree.query(target, 3))
    assert small <= large


def test_classic_typo_correction_example():
    tree = BKTree(levenshtein)
    for w in ["receive", "receipt", "deceive", "perceive", "believe"]:
        tree.insert(w)
    results = tree.query("recieve", 2)
    assert "receive" in results
