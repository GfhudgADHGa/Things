import pytest

from vcs.objects import ObjectStore
from vcs.tree import TreeEntry, checkout_tree, deserialize_tree, flatten_tree, serialize_tree, write_tree


def test_serialize_deserialize_round_trip():
    entries = [
        TreeEntry("b.txt", "blob", "h2"),
        TreeEntry("a.txt", "blob", "h1"),
        TreeEntry("sub", "tree", "h3"),
    ]
    data = serialize_tree(entries)
    restored = deserialize_tree(data)
    assert sorted(restored, key=lambda e: e.name) == sorted(entries, key=lambda e: e.name)


def test_serialize_is_sorted_by_name_regardless_of_input_order():
    entries_a = [TreeEntry("z.txt", "blob", "h1"), TreeEntry("a.txt", "blob", "h2")]
    entries_b = [TreeEntry("a.txt", "blob", "h2"), TreeEntry("z.txt", "blob", "h1")]
    assert serialize_tree(entries_a) == serialize_tree(entries_b)


def _no_ignore(path):
    return False


def test_write_tree_and_read_tree_round_trip(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("A")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_text("B")

    store = ObjectStore(tmp_path / "objects")
    tree_hash = write_tree(store, src, _no_ignore)

    flat = flatten_tree(store, tree_hash)
    assert set(flat.keys()) == {"a.txt", "sub/b.txt"}


def test_identical_directory_contents_hash_the_same(tmp_path):
    src1, src2 = tmp_path / "src1", tmp_path / "src2"
    for src in (src1, src2):
        src.mkdir()
        (src / "a.txt").write_text("same")
        (src / "sub").mkdir()
        (src / "sub" / "b.txt").write_text("also same")

    store = ObjectStore(tmp_path / "objects")
    hash1 = write_tree(store, src1, _no_ignore)
    hash2 = write_tree(store, src2, _no_ignore)
    assert hash1 == hash2


def test_checkout_reproduces_directory_byte_for_byte(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello\x00world")
    (src / "sub").mkdir()
    (src / "sub" / "deep").mkdir()
    (src / "sub" / "deep" / "c.txt").write_text("deeply nested")

    store = ObjectStore(tmp_path / "objects")
    tree_hash = write_tree(store, src, _no_ignore)

    dest = tmp_path / "checkout"
    checkout_tree(store, tree_hash, dest)

    assert (dest / "a.txt").read_bytes() == b"hello\x00world"
    assert (dest / "sub" / "deep" / "c.txt").read_text() == "deeply nested"


def test_empty_directory_produces_empty_tree(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    store = ObjectStore(tmp_path / "objects")
    tree_hash = write_tree(store, src, _no_ignore)
    assert flatten_tree(store, tree_hash) == {}


def test_write_tree_respects_ignore_predicate(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "keep.txt").write_text("keep")
    (src / "skip.txt").write_text("skip")

    store = ObjectStore(tmp_path / "objects")
    tree_hash = write_tree(store, src, lambda p: p.name == "skip.txt")
    assert set(flatten_tree(store, tree_hash).keys()) == {"keep.txt"}


def test_read_tree_on_a_blob_raises(tmp_path):
    from vcs.tree import read_tree
    store = ObjectStore(tmp_path / "objects")
    blob_hash = store.store("blob", b"not a tree")
    with pytest.raises(ValueError):
        read_tree(store, blob_hash)
