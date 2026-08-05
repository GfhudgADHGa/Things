"""The main correctness proof for this thing: round-trip fidelity.
Commit an arbitrary (including randomly generated) nested directory
tree, check it out into a completely fresh directory, and require the
result to be byte-for-byte identical to the original -- structure,
filenames, and file contents, including binary data. This is the same
"does the whole pipeline actually preserve what you put into it" idea as
kvstore's crash-recovery tests and jpeg's Pillow round-trip, applied to
a version control system's actual job: never silently losing or
corrupting committed content.
"""
import random
from pathlib import Path

import pytest

from vcs import Repository, RepositoryError
from vcs.diff import diff_trees
from vcs.commit import read_commit


def _random_tree(root: Path, rng: random.Random, depth: int = 0, max_depth: int = 3) -> None:
    root.mkdir(parents=True, exist_ok=True)
    num_files = rng.randint(0, 4)
    for i in range(num_files):
        name = f"file_{depth}_{i}_{rng.randint(0, 999999)}.dat"
        length = rng.randint(0, 200)
        (root / name).write_bytes(bytes(rng.randrange(256) for _ in range(length)))
    if depth < max_depth:
        num_dirs = rng.randint(0, 2)
        for i in range(num_dirs):
            _random_tree(root / f"dir_{depth}_{i}", rng, depth + 1, max_depth)


def _collect_files(root: Path) -> dict:
    """{relative_path_str: content_bytes} for every file under root,
    skipping .vcs -- an independent way of reading back "what's actually
    on disk" that doesn't go through any vcs code at all."""
    result = {}
    for path in root.rglob("*"):
        if path.is_file() and ".vcs" not in path.relative_to(root).parts:
            result[str(path.relative_to(root))] = path.read_bytes()
    return result


def test_round_trip_a_simple_tree(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("hello")
    (repo_dir / "sub").mkdir()
    (repo_dir / "sub" / "b.txt").write_text("world")

    commit_hash = repo.commit("initial")

    checkout_dir = tmp_path / "checkout"
    repo.checkout(commit_hash, checkout_dir)

    assert _collect_files(checkout_dir) == _collect_files(repo_dir)


def test_round_trip_binary_content_including_null_bytes(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "binary.dat").write_bytes(bytes(range(256)) * 10)

    commit_hash = repo.commit("binary content")
    checkout_dir = tmp_path / "checkout"
    repo.checkout(commit_hash, checkout_dir)

    assert (checkout_dir / "binary.dat").read_bytes() == (repo_dir / "binary.dat").read_bytes()


def test_round_trip_empty_file(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "empty.txt").write_bytes(b"")

    commit_hash = repo.commit("empty file")
    checkout_dir = tmp_path / "checkout"
    repo.checkout(commit_hash, checkout_dir)

    assert (checkout_dir / "empty.txt").read_bytes() == b""


def test_round_trip_empty_repository(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    commit_hash = repo.commit("nothing here")
    checkout_dir = tmp_path / "checkout"
    repo.checkout(commit_hash, checkout_dir)
    assert _collect_files(checkout_dir) == {}


@pytest.mark.parametrize("seed", range(40))
def test_fuzz_random_directory_trees_round_trip_exactly(tmp_path, seed):
    rng = random.Random(seed)
    repo_dir = tmp_path / f"repo_{seed}"
    repo = Repository.init(repo_dir)
    _random_tree(repo_dir, rng)

    commit_hash = repo.commit("random tree")
    checkout_dir = tmp_path / f"checkout_{seed}"
    repo.checkout(commit_hash, checkout_dir)

    assert _collect_files(checkout_dir) == _collect_files(repo_dir)


def test_older_commit_is_still_checkoutable_after_later_commits(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("version 1")
    c1 = repo.commit("v1")

    (repo_dir / "a.txt").write_text("version 2")
    repo.commit("v2")

    checkout_dir = tmp_path / "checkout_v1"
    repo.checkout(c1, checkout_dir)
    assert (checkout_dir / "a.txt").read_text() == "version 1"


# ---- content-addressing / dedup ----

def test_identical_files_are_deduplicated_in_storage(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("duplicate content")
    (repo_dir / "b.txt").write_text("duplicate content")
    repo.commit("two identical files")
    # exactly one blob (shared), one tree, one commit
    assert repo.store.count() == 3


def test_recommitting_unchanged_content_does_not_grow_the_store(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("unchanged")
    repo.commit("first")
    count_after_first = repo.store.count()

    repo.commit("second, but nothing actually changed")
    # new commit object only (new timestamp/parent -> new commit hash);
    # the blob and tree are identical and must not be duplicated
    assert repo.store.count() == count_after_first + 1


# ---- log / history ----

def test_log_lists_commits_newest_first(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("1")
    repo.commit("first")
    (repo_dir / "a.txt").write_text("2")
    repo.commit("second")

    messages = [c.message for c in repo.log()]
    assert messages == ["second", "first"]


def test_log_on_empty_repository_is_empty(tmp_path):
    repo = Repository.init(tmp_path / "repo")
    assert repo.log() == []


# ---- branches and merges ----

def test_create_and_switch_branch(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("main content")
    repo.commit("main commit")

    repo.create_branch("feature")
    repo.switch_branch("feature")
    assert repo.current_branch() == "feature"
    assert repo.head_commit() == repo._branch_ref_path("main").read_text().strip()


def test_switching_to_unknown_branch_raises(tmp_path):
    repo = Repository.init(tmp_path / "repo")
    with pytest.raises(RepositoryError):
        repo.switch_branch("nonexistent")


def test_merge_creates_a_two_parent_commit_and_history_includes_both_branches(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "base.txt").write_text("base")
    repo.commit("base commit")

    repo.create_branch("feature")
    repo.switch_branch("feature")
    (repo_dir / "feature.txt").write_text("feature work")
    feature_commit = repo.commit("feature commit")

    repo.switch_branch("main")
    (repo_dir / "main.txt").write_text("main work")
    main_commit = repo.commit("main commit")

    (repo_dir / "feature.txt").write_text("feature work")  # bring it into the working dir for the merge
    merge_commit = repo.merge("feature", "merge feature into main")

    merge_obj = read_commit(repo.store, merge_commit)
    assert set(merge_obj.parent_hashes) == {main_commit, feature_commit}

    history_hashes = {c.message for c in repo.log()}
    assert history_hashes == {"base commit", "feature commit", "main commit", "merge feature into main"}


def test_diff_between_commits_via_repository(tmp_path):
    repo_dir = tmp_path / "repo"
    repo = Repository.init(repo_dir)
    (repo_dir / "a.txt").write_text("v1")
    c1 = repo.commit("v1")
    (repo_dir / "a.txt").write_text("v2")
    (repo_dir / "b.txt").write_text("new file")
    c2 = repo.commit("v2")

    tree1 = read_commit(repo.store, c1).tree_hash
    tree2 = read_commit(repo.store, c2).tree_hash
    changes = diff_trees(repo.store, tree1, tree2)
    assert ("modified", "a.txt") in changes
    assert ("added", "b.txt") in changes
