import pytest

from vcs.commit import Commit, commit_history, deserialize_commit, read_commit, serialize_commit, write_commit
from vcs.objects import ObjectStore


def test_serialize_deserialize_round_trip():
    c = Commit(tree_hash="abc123", parent_hashes=("p1", "p2"), message="a message\nwith newlines", timestamp=1234.5)
    restored = deserialize_commit(serialize_commit(c))
    assert restored == c


def test_serialize_deserialize_no_parents():
    c = Commit(tree_hash="abc123", parent_hashes=(), message="root commit", timestamp=0.0)
    assert deserialize_commit(serialize_commit(c)) == c


def test_message_with_blank_lines_round_trips():
    c = Commit("t", (), "summary line\n\nbody paragraph\n\nmore body", 1.0)
    assert deserialize_commit(serialize_commit(c)).message == c.message


def test_missing_tree_header_raises():
    with pytest.raises(ValueError):
        deserialize_commit(b"parent abc\n\nmessage")


def test_write_and_read_commit(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    c = Commit("treehash", (), "msg", 42.0)
    h = write_commit(store, c)
    assert read_commit(store, h) == c


def test_read_commit_on_a_blob_raises(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    blob_hash = store.store("blob", b"not a commit")
    with pytest.raises(ValueError):
        read_commit(store, blob_hash)


# ---- commit_history / DAG traversal ----

def _make_chain(store, length):
    """A linear chain of `length` commits; returns the list of hashes,
    oldest first."""
    hashes = []
    parent = ()
    for i in range(length):
        h = write_commit(store, Commit(f"tree{i}", parent, f"commit {i}", float(i)))
        hashes.append(h)
        parent = (h,)
    return hashes


def test_history_of_a_single_commit(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    h = write_commit(store, Commit("t", (), "root", 0.0))
    assert commit_history(store, h) == [h]


def test_history_of_a_linear_chain_is_newest_first(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    hashes = _make_chain(store, 5)
    history = commit_history(store, hashes[-1])
    assert history == list(reversed(hashes))


def test_history_visits_every_commit_before_its_parents(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    hashes = _make_chain(store, 8)
    history = commit_history(store, hashes[-1])
    position = {h: i for i, h in enumerate(history)}
    for i in range(len(hashes) - 1):
        child, parent = hashes[i + 1], hashes[i]
        assert position[child] < position[parent]


def test_diamond_merge_history_includes_each_commit_exactly_once(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    root = write_commit(store, Commit("t0", (), "root", 0.0))
    left = write_commit(store, Commit("t1", (root,), "left branch", 1.0))
    right = write_commit(store, Commit("t2", (root,), "right branch", 2.0))
    merge = write_commit(store, Commit("t3", (left, right), "merge", 3.0))

    history = commit_history(store, merge)
    assert set(history) == {root, left, right, merge}
    assert len(history) == 4  # root is a shared ancestor, must not be counted twice

    position = {h: i for i, h in enumerate(history)}
    assert position[merge] < position[left]
    assert position[merge] < position[right]
    assert position[left] < position[root]
    assert position[right] < position[root]


def test_history_matches_brute_force_reachability(tmp_path):
    # An independent, more obviously-correct (if inefficient) way to
    # compute "every ancestor": recursively union each parent's ancestor
    # set. commit_history() should visit exactly this same set of nodes.
    store = ObjectStore(tmp_path / "objects")
    root = write_commit(store, Commit("t0", (), "root", 0.0))
    a = write_commit(store, Commit("t1", (root,), "a", 1.0))
    b = write_commit(store, Commit("t2", (root,), "b", 2.0))
    c = write_commit(store, Commit("t3", (a,), "c", 3.0))
    merge = write_commit(store, Commit("t4", (c, b), "merge", 4.0))

    def brute_force_ancestors(commit_hash):
        commit = read_commit(store, commit_hash)
        result = {commit_hash}
        for parent in commit.parent_hashes:
            result |= brute_force_ancestors(parent)
        return result

    assert set(commit_history(store, merge)) == brute_force_ancestors(merge)


def test_long_chain_does_not_hit_recursion_limit(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    hashes = _make_chain(store, 5000)
    history = commit_history(store, hashes[-1])
    assert len(history) == 5000
