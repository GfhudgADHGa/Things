import pytest

from vcs.objects import ObjectStore, hash_object


def test_store_and_load_round_trips(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    h = store.store("blob", b"hello world")
    obj_type, content = store.load(h)
    assert obj_type == "blob"
    assert content == b"hello world"


def test_hash_is_deterministic():
    assert hash_object("blob", b"hello") == hash_object("blob", b"hello")


def test_different_content_gives_different_hash():
    assert hash_object("blob", b"hello") != hash_object("blob", b"world")


def test_different_type_gives_different_hash_for_same_content():
    # the header includes the type, so a blob and a tree with
    # byte-identical "content" still hash differently
    assert hash_object("blob", b"same bytes") != hash_object("tree", b"same bytes")


def test_identical_content_is_stored_only_once(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    h1 = store.store("blob", b"duplicate content")
    h2 = store.store("blob", b"duplicate content")
    assert h1 == h2
    assert store.count() == 1


def test_empty_content_round_trips(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    h = store.store("blob", b"")
    assert store.load(h) == ("blob", b"")


def test_binary_content_with_embedded_nulls_round_trips(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    data = bytes(range(256)) * 4  # includes 0x00 bytes, which the header parser must not confuse with the header terminator
    h = store.store("blob", data)
    assert store.load(h) == ("blob", data)


def test_loading_unknown_hash_raises(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    with pytest.raises(KeyError):
        store.load("0" * 64)


def test_exists(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    h = store.store("blob", b"x")
    assert store.exists(h) is True
    assert store.exists("f" * 64) is False
