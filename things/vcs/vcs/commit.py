"""Commit objects: a tree hash, zero or more parent commit hashes (zero
for the first commit, one for a normal commit, two-or-more for a merge),
a message, and a timestamp -- plus commit_history(), a DAG traversal
over parent pointers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .objects import ObjectStore


@dataclass(frozen=True)
class Commit:
    tree_hash: str
    parent_hashes: Tuple[str, ...]
    message: str
    timestamp: float


def serialize_commit(commit: Commit) -> bytes:
    lines = [f"tree {commit.tree_hash}\n"]
    lines.extend(f"parent {parent}\n" for parent in commit.parent_hashes)
    lines.append(f"timestamp {commit.timestamp}\n")
    lines.append("\n")
    lines.append(commit.message)
    return "".join(lines).encode()


def deserialize_commit(content: bytes) -> Commit:
    header, _, message = content.decode().partition("\n\n")
    tree_hash = None
    parents: List[str] = []
    timestamp = 0.0
    for line in header.splitlines():
        key, _, value = line.partition(" ")
        if key == "tree":
            tree_hash = value
        elif key == "parent":
            parents.append(value)
        elif key == "timestamp":
            timestamp = float(value)
    if tree_hash is None:
        raise ValueError("commit object is missing its tree header")
    return Commit(tree_hash, tuple(parents), message, timestamp)


def write_commit(store: ObjectStore, commit: Commit) -> str:
    return store.store("commit", serialize_commit(commit))


def read_commit(store: ObjectStore, commit_hash: str) -> Commit:
    obj_type, content = store.load(commit_hash)
    if obj_type != "commit":
        raise ValueError(f"object {commit_hash} is not a commit (got {obj_type!r})")
    return deserialize_commit(content)


def commit_history(store: ObjectStore, start_hash: str) -> List[str]:
    """Every ancestor of start_hash (including itself), each appearing
    exactly once, with every commit appearing before all of its parents.

    This needs a real topological sort, not just "DFS, skip anything
    already visited": a first attempt did exactly that simpler thing and
    failed on diamond-shaped history (two branches merging back into a
    shared ancestor) -- whichever branch's DFS happened to reach the
    shared ancestor first could emit it before the *other* branch that
    also points to it, even though that other branch hadn't been emitted
    yet itself. See test_commit.py's diamond-history test, which is
    exactly what caught this. The fix is the standard one: a DFS
    post-order (append a node only after all of its parents have been
    fully processed), then reverse it -- done iteratively, with an
    explicit stack of (node, "have its parents been pushed yet") frames,
    so a very long or very wide history can't hit Python's recursion
    limit the way a naive recursive post-order would.
    """
    postorder: List[str] = []
    visited = set()
    stack = [(start_hash, False)]
    while stack:
        node, parents_pushed = stack.pop()
        if parents_pushed:
            postorder.append(node)
            continue
        if node in visited:
            continue
        visited.add(node)
        stack.append((node, True))
        commit = read_commit(store, node)
        for parent in commit.parent_hashes:
            if parent not in visited:
                stack.append((parent, False))
    postorder.reverse()
    return postorder
