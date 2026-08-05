"""The whole point of a write-ahead log is surviving a crash. These tests
simulate one directly: write real records with a real KVStore, close it
(so we know exactly what's on disk), then hand-corrupt the file the way an
interrupted write or a bit of disk corruption would, and verify recovery
is clean -- no exception, no data loss for the valid prefix, and no
lingering garbage left in the file to confuse a future recovery.
"""
import os

import pytest

from kvstore import KVStore
from kvstore.record import encode_record, OP_PUT


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "test.db")


def _write_and_close(path, pairs):
    db = KVStore(path)
    for k, v in pairs:
        db.put(k, v)
    db.close()
    return os.path.getsize(path)


def test_recovers_cleanly_from_a_torn_final_record(path):
    good_size = _write_and_close(path, [("a", "1"), ("b", "2"), ("c", "3")])

    # simulate the process dying mid-write() of a 4th record: a length
    # prefix and checksum are present, but the body is cut short
    torn = encode_record(OP_PUT, b"d", b"this write never finished")[:15]
    with open(path, "ab") as f:
        f.write(torn)
    assert os.path.getsize(path) > good_size

    db = KVStore(path)  # must not raise
    assert sorted(db.keys()) == ["a", "b", "c"]
    assert db.get("a") == "1"
    assert db.get("b") == "2"
    assert db.get("c") == "3"
    assert db.get("d") is None
    db.close()


def test_torn_write_is_truncated_from_disk_on_recovery(path):
    good_size = _write_and_close(path, [("a", "1")])
    with open(path, "ab") as f:
        f.write(b"\x00\x00\x01\x00garbage-header-claims-256-byte-body-but-isnt")

    db = KVStore(path)
    db.close()
    assert os.path.getsize(path) == good_size


def test_recovers_from_corrupted_checksum_in_final_record(path):
    good_size = _write_and_close(path, [("a", "1"), ("b", "2")])

    # flip a bit inside what was a well-formed, fully-written record
    with open(path, "r+b") as f:
        f.seek(-1, os.SEEK_END)
        last_byte = f.read(1)
        f.seek(-1, os.SEEK_END)
        f.write(bytes([last_byte[0] ^ 0xFF]))

    db = KVStore(path)
    assert db.get("a") == "1"
    assert db.get("b") is None  # the corrupted record is discarded
    db.close()
    assert os.path.getsize(path) < good_size


def test_store_remains_writable_after_recovering_from_corruption(path):
    _write_and_close(path, [("a", "1")])
    with open(path, "ab") as f:
        f.write(b"not a valid record at all, just noise")

    db = KVStore(path)
    db.put("b", "2")  # new writes after a corrupt recovery must still work
    db.close()

    reopened = KVStore(path)
    assert reopened.get("a") == "1"
    assert reopened.get("b") == "2"
    reopened.close()


def test_empty_file_recovers_to_empty_store(path):
    open(path, "wb").close()
    db = KVStore(path)
    assert len(db) == 0
    db.close()


def test_file_of_pure_garbage_recovers_to_empty_store_not_a_crash(path):
    with open(path, "wb") as f:
        f.write(os.urandom(500))

    db = KVStore(path)  # must not raise, even on totally nonsensical bytes
    assert len(db) == 0
    db.close()
    assert os.path.getsize(path) == 0  # all garbage truncated away


def test_recovery_replays_deletes_correctly_even_with_trailing_garbage(path):
    good_size = _write_and_close(path, [("a", "1"), ("b", "2")])
    db = KVStore(path)
    db.delete("a")
    db.close()

    with open(path, "ab") as f:
        f.write(b"\xff" * 10)

    reopened = KVStore(path)
    assert "a" not in reopened
    assert reopened.get("b") == "2"
    reopened.close()


def test_crash_mid_compaction_never_loses_the_original_log(path, monkeypatch):
    db = KVStore(path)
    db.put("a", "1")
    db.put("b", "2")
    db.close()

    original_bytes = open(path, "rb").read()

    # simulate a crash that happens after the compacted temp file is written
    # but before the atomic rename -- os.replace should never even be
    # reached, so the live log must be completely untouched
    def boom(*args, **kwargs):
        raise OSError("simulated crash before rename")

    db = KVStore(path)
    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        db.compact()

    # the original log on disk is exactly as it was -- compaction never
    # got far enough to touch it
    assert open(path, "rb").read() == original_bytes

    monkeypatch.undo()
    db.close()
    reopened = KVStore(path)
    assert reopened.get("a") == "1"
    assert reopened.get("b") == "2"
    reopened.close()
