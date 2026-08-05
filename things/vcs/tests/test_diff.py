from vcs.diff import diff_trees
from vcs.objects import ObjectStore
from vcs.tree import TreeEntry, serialize_tree


def _make_tree(store, entries):
    return store.store("tree", serialize_tree(entries))


def test_diff_detects_added_file(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob = store.store("blob", b"content")
    tree_a = _make_tree(store, [])
    tree_b = _make_tree(store, [TreeEntry("new.txt", "blob", blob)])
    assert diff_trees(store, tree_a, tree_b) == [("added", "new.txt")]


def test_diff_detects_removed_file(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob = store.store("blob", b"content")
    tree_a = _make_tree(store, [TreeEntry("old.txt", "blob", blob)])
    tree_b = _make_tree(store, [])
    assert diff_trees(store, tree_a, tree_b) == [("removed", "old.txt")]


def test_diff_detects_modified_file(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob1 = store.store("blob", b"version 1")
    blob2 = store.store("blob", b"version 2")
    tree_a = _make_tree(store, [TreeEntry("f.txt", "blob", blob1)])
    tree_b = _make_tree(store, [TreeEntry("f.txt", "blob", blob2)])
    assert diff_trees(store, tree_a, tree_b) == [("modified", "f.txt")]


def test_diff_of_identical_trees_is_empty(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob = store.store("blob", b"same")
    tree_a = _make_tree(store, [TreeEntry("f.txt", "blob", blob)])
    tree_b = _make_tree(store, [TreeEntry("f.txt", "blob", blob)])
    assert diff_trees(store, tree_a, tree_b) == []


def test_diff_handles_nested_subdirectories(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob1 = store.store("blob", b"v1")
    blob2 = store.store("blob", b"v2")
    sub_a = _make_tree(store, [TreeEntry("nested.txt", "blob", blob1)])
    sub_b = _make_tree(store, [TreeEntry("nested.txt", "blob", blob2)])
    tree_a = _make_tree(store, [TreeEntry("sub", "tree", sub_a)])
    tree_b = _make_tree(store, [TreeEntry("sub", "tree", sub_b)])
    assert diff_trees(store, tree_a, tree_b) == [("modified", "sub/nested.txt")]


def test_diff_results_are_sorted_by_path(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob = store.store("blob", b"x")
    tree_a = _make_tree(store, [])
    tree_b = _make_tree(store, [
        TreeEntry("z.txt", "blob", blob),
        TreeEntry("a.txt", "blob", blob),
        TreeEntry("m.txt", "blob", blob),
    ])
    result = diff_trees(store, tree_a, tree_b)
    assert [path for _, path in result] == ["a.txt", "m.txt", "z.txt"]
