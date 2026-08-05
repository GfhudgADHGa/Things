"""File-level diffing between two committed trees: which paths were
added, removed, or modified. Deliberately file-level (matching blob
hashes), not line-level -- `difftool` elsewhere in this collection
already does line-level Myers diffing and there's no need to duplicate
that here; this is about identifying *which files* changed between two
snapshots, which is what git's own `diff --stat`/`status` are for.
"""
from __future__ import annotations

from typing import List, Tuple

from .objects import ObjectStore
from .tree import flatten_tree


def diff_trees(store: ObjectStore, tree_hash_a: str, tree_hash_b: str) -> List[Tuple[str, str]]:
    """Returns a sorted list of (status, path) pairs, status in
    {"added", "removed", "modified"}."""
    files_a = flatten_tree(store, tree_hash_a)
    files_b = flatten_tree(store, tree_hash_b)
    changes = []
    for path in sorted(set(files_a) | set(files_b)):
        hash_a, hash_b = files_a.get(path), files_b.get(path)
        if hash_a is None:
            changes.append(("added", path))
        elif hash_b is None:
            changes.append(("removed", path))
        elif hash_a != hash_b:
            changes.append(("modified", path))
    return changes
