import os

import pytest

from kvstore import KVStore


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "test.db")


def test_put_and_get(path):
    db = KVStore(path)
    db.put("a", "1")
    assert db.get("a") == "1"
    db.close()


def test_get_missing_key_returns_none(path):
    db = KVStore(path)
    assert db.get("nope") is None
    db.close()


def test_overwrite_keeps_latest_value(path):
    db = KVStore(path)
    db.put("a", "1")
    db.put("a", "2")
    assert db.get("a") == "2"
    db.close()


def test_delete_removes_key(path):
    db = KVStore(path)
    db.put("a", "1")
    db.delete("a")
    assert db.get("a") is None
    assert "a" not in db
    db.close()


def test_delete_of_missing_key_is_a_no_op(path):
    db = KVStore(path)
    db.delete("nope")  # should not raise
    db.close()


def test_len_and_contains_and_keys(path):
    db = KVStore(path)
    db.put("a", "1")
    db.put("b", "2")
    assert len(db) == 2
    assert "a" in db
    assert sorted(db.keys()) == ["a", "b"]
    db.close()


def test_context_manager_closes_file(path):
    with KVStore(path) as db:
        db.put("a", "1")
    # a fresh store on the same path should see the persisted value
    db2 = KVStore(path)
    assert db2.get("a") == "1"
    db2.close()


def test_persistence_across_reopen(path):
    db = KVStore(path)
    db.put("a", "1")
    db.put("b", "2")
    db.delete("a")
    db.put("c", "3")
    db.close()

    reopened = KVStore(path)
    assert reopened.get("a") is None
    assert reopened.get("b") == "2"
    assert reopened.get("c") == "3"
    assert sorted(reopened.keys()) == ["b", "c"]
    reopened.close()


def test_opening_nonexistent_path_creates_empty_store(path):
    assert not os.path.exists(path)
    db = KVStore(path)
    assert len(db) == 0
    assert os.path.exists(path)
    db.close()


def test_every_write_is_fsynced_to_disk(path):
    # not directly observable from Python, but we can at least confirm the
    # file grows immediately with each write rather than being buffered
    db = KVStore(path)
    size0 = os.path.getsize(path)
    db.put("a", "1")
    size1 = os.path.getsize(path)
    assert size1 > size0
    db.close()


def test_compact_shrinks_log_after_overwrites(path):
    db = KVStore(path)
    for i in range(50):
        db.put("a", str(i))  # 50 writes to the same key
    size_before = os.path.getsize(path)
    db.compact()
    size_after = os.path.getsize(path)
    assert size_after < size_before
    assert db.get("a") == "49"
    db.close()


def test_compact_drops_deleted_keys(path):
    db = KVStore(path)
    db.put("a", "1")
    db.put("b", "2")
    db.delete("a")
    db.compact()
    assert "a" not in db
    assert db.get("b") == "2"
    db.close()

    reopened = KVStore(path)
    assert "a" not in reopened
    assert reopened.get("b") == "2"
    reopened.close()


def test_compact_preserves_state_across_reopen(path):
    db = KVStore(path)
    for i in range(20):
        db.put(f"key{i}", f"value{i}")
    db.delete("key5")
    db.put("key3", "updated")
    expected = dict(db.index)
    db.compact()
    db.close()

    reopened = KVStore(path)
    assert reopened.index == expected
    reopened.close()


def test_store_usable_immediately_after_compact(path):
    db = KVStore(path)
    db.put("a", "1")
    db.compact()
    db.put("b", "2")  # writes after compact must still work (file handle refreshed)
    assert db.get("a") == "1"
    assert db.get("b") == "2"
    db.close()

    reopened = KVStore(path)
    assert reopened.get("a") == "1"
    assert reopened.get("b") == "2"
    reopened.close()


def test_binary_unsafe_but_unicode_values_roundtrip(path):
    db = KVStore(path)
    db.put("emoji", "hello 🌍 world")
    db.close()
    reopened = KVStore(path)
    assert reopened.get("emoji") == "hello 🌍 world"
    reopened.close()
