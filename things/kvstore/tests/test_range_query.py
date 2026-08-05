import random
import string

import pytest

from kvstore import KVStore


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "test.db")


def _populated(path, keys):
    db = KVStore(path)
    for k in keys:
        db.put(k, k.upper())
    return db


def test_full_range_returns_everything_sorted(path):
    db = _populated(path, ["banana", "apple", "cherry"])
    assert db.range_query() == [("apple", "APPLE"), ("banana", "BANANA"), ("cherry", "CHERRY")]
    db.close()


def test_range_is_start_inclusive_end_exclusive(path):
    db = _populated(path, ["a", "b", "c", "d", "e"])
    assert db.range_query("b", "d") == [("b", "B"), ("c", "C")]
    db.close()


def test_range_with_only_start(path):
    db = _populated(path, ["a", "b", "c", "d"])
    assert db.range_query(start_key="c") == [("c", "C"), ("d", "D")]
    db.close()


def test_range_with_only_end(path):
    db = _populated(path, ["a", "b", "c", "d"])
    assert db.range_query(end_key="c") == [("a", "A"), ("b", "B")]
    db.close()


def test_range_matching_nothing_is_empty(path):
    db = _populated(path, ["a", "b", "c"])
    assert db.range_query("x", "z") == []
    db.close()


def test_range_on_empty_store(path):
    db = KVStore(path)
    assert db.range_query() == []
    db.close()


def test_range_excludes_deleted_keys(path):
    db = _populated(path, ["a", "b", "c"])
    db.delete("b")
    assert db.range_query() == [("a", "A"), ("c", "C")]
    db.close()


def test_range_reflects_overwritten_values(path):
    db = _populated(path, ["a", "b"])
    db.put("a", "UPDATED")
    assert db.range_query() == [("a", "UPDATED"), ("b", "B")]
    db.close()


def test_range_boundary_key_is_included_at_start_excluded_at_end(path):
    db = _populated(path, ["a", "b", "c"])
    assert ("b", "B") in db.range_query("b", "c")
    assert ("c", "C") not in db.range_query("a", "c")
    db.close()


def test_range_matches_naive_filter_sort_baseline(path):
    random.seed(0)
    keys = list({"".join(random.choices(string.ascii_lowercase, k=3)) for _ in range(100)})
    db = _populated(path, keys)

    start, end = "h", "r"
    expected = sorted((k, k.upper()) for k in keys if start <= k < end)
    assert db.range_query(start, end) == expected
    db.close()


def test_range_survives_reopen(path):
    db = _populated(path, ["a", "b", "c"])
    db.close()
    reopened = KVStore(path)
    assert reopened.range_query() == [("a", "A"), ("b", "B"), ("c", "C")]
    reopened.close()
