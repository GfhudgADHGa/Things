import random

import pytest

from minidb.btree import BTree


def test_empty_tree():
    tree = BTree()
    assert len(tree) == 0
    assert tree.in_order() == []
    assert tree.search_equal(5) == []


def test_single_insert_and_search():
    tree = BTree(min_degree=2)
    tree.insert(10, 0)
    assert tree.search_equal(10) == [0]
    assert tree.search_equal(11) == []


def test_duplicate_values_are_all_retained():
    tree = BTree(min_degree=2)
    tree.insert(5, 0)
    tree.insert(5, 1)
    tree.insert(5, 2)
    assert sorted(tree.search_equal(5)) == [0, 1, 2]
    assert len(tree) == 3


@pytest.mark.parametrize("min_degree", [2, 3, 4, 16])
def test_in_order_traversal_is_sorted_for_various_degrees(min_degree):
    rng = random.Random(min_degree)
    tree = BTree(min_degree=min_degree)
    data = [(rng.randint(0, 100), i) for i in range(500)]
    for value, row_id in data:
        tree.insert(value, row_id)
    result = tree.in_order()
    assert result == sorted(data)
    assert len(result) == len(data)


@pytest.mark.parametrize("seed", range(30))
def test_equality_search_matches_brute_force(seed):
    rng = random.Random(seed)
    tree = BTree(min_degree=rng.choice([2, 3, 5, 10]))
    n = rng.randint(0, 400)
    data = [(rng.randint(0, 50), i) for i in range(n)]
    for value, row_id in data:
        tree.insert(value, row_id)

    for target in range(-5, 55):
        expected = sorted(rid for v, rid in data if v == target)
        actual = sorted(tree.search_equal(target))
        assert actual == expected, (seed, target)


@pytest.mark.parametrize("seed", range(30))
def test_range_search_matches_brute_force(seed):
    rng = random.Random(seed + 1000)
    tree = BTree(min_degree=rng.choice([2, 3, 5, 10]))
    n = rng.randint(0, 400)
    data = [(rng.randint(0, 50), i) for i in range(n)]
    for value, row_id in data:
        tree.insert(value, row_id)

    bounds = [(None, None), (None, 20), (20, None), (10, 30), (49, 50), (-10, -1), (25, 25)]
    for low, high in bounds:
        expected = sorted((v, rid) for v, rid in data if (low is None or v >= low) and (high is None or v <= high))
        actual = sorted(tree.range_search(low, high))
        assert actual == expected, (seed, low, high)


def test_insert_forces_root_split():
    # min_degree=2 means a node overflows at 3 entries; insert enough to
    # force multiple levels of splitting and check nothing gets lost.
    tree = BTree(min_degree=2)
    for i in range(100):
        tree.insert(i, i)
    assert len(tree) == 100
    assert [v for v, _ in tree.in_order()] == list(range(100))


def test_string_values_work_too():
    tree = BTree(min_degree=2)
    words = ["banana", "apple", "cherry", "date", "apple"]
    for i, w in enumerate(words):
        tree.insert(w, i)
    assert sorted(tree.search_equal("apple")) == [1, 4]
    assert [v for v, _ in tree.in_order()] == sorted(words)


def test_min_degree_below_two_raises():
    with pytest.raises(ValueError):
        BTree(min_degree=1)


def test_large_random_tree_is_internally_consistent():
    rng = random.Random(42)
    tree = BTree(min_degree=8)
    data = [(rng.randint(0, 1000), i) for i in range(5000)]
    for value, row_id in data:
        tree.insert(value, row_id)
    assert tree.in_order() == sorted(data)
