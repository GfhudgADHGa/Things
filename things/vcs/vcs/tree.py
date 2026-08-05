"""Tree objects: a snapshot of a directory's structure. Each entry maps
a name to either a blob (file) or another tree (subdirectory),
identified by that entry's own content hash. Entries are always
serialized in name-sorted order specifically so that two directories
with identical contents -- regardless of what order the filesystem
happened to list them in -- always hash to the exact same tree object.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from .objects import ObjectStore


@dataclass(frozen=True)
class TreeEntry:
    name: str
    entry_type: str  # "blob" or "tree"
    object_hash: str


def serialize_tree(entries: List[TreeEntry]) -> bytes:
    lines = [f"{e.entry_type} {e.object_hash} {e.name}\n" for e in sorted(entries, key=lambda e: e.name)]
    return "".join(lines).encode()


def deserialize_tree(content: bytes) -> List[TreeEntry]:
    entries = []
    text = content.decode()
    for line in text.splitlines():
        entry_type, object_hash, name = line.split(" ", 2)
        entries.append(TreeEntry(name, entry_type, object_hash))
    return entries


def write_tree(store: ObjectStore, directory: Path, ignore: Callable[[Path], bool]) -> str:
    """Recursively hashes `directory`'s contents into blob/tree objects,
    returning the root tree's hash."""
    entries = []
    for path in sorted(directory.iterdir()):
        if ignore(path):
            continue
        if path.is_dir():
            sub_hash = write_tree(store, path, ignore)
            entries.append(TreeEntry(path.name, "tree", sub_hash))
        else:
            blob_hash = store.store("blob", path.read_bytes())
            entries.append(TreeEntry(path.name, "blob", blob_hash))
    return store.store("tree", serialize_tree(entries))


def read_tree(store: ObjectStore, tree_hash: str) -> List[TreeEntry]:
    obj_type, content = store.load(tree_hash)
    if obj_type != "tree":
        raise ValueError(f"object {tree_hash} is not a tree (got {obj_type!r})")
    return deserialize_tree(content)


def checkout_tree(store: ObjectStore, tree_hash: str, target_dir: Path) -> None:
    """Writes the tree's contents into target_dir, which should be
    empty/fresh -- this overlays files but never deletes anything
    already present, unlike a real `git checkout`'s working-tree reset."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in read_tree(store, tree_hash):
        target_path = target_dir / entry.name
        if entry.entry_type == "tree":
            checkout_tree(store, entry.object_hash, target_path)
        else:
            _obj_type, content = store.load(entry.object_hash)
            target_path.write_bytes(content)


def flatten_tree(store: ObjectStore, tree_hash: str, prefix: str = "") -> dict:
    """Every file in the tree (recursively), as {relative_path: blob_hash}."""
    result = {}
    for entry in read_tree(store, tree_hash):
        path = f"{prefix}{entry.name}"
        if entry.entry_type == "tree":
            result.update(flatten_tree(store, entry.object_hash, prefix=path + "/"))
        else:
            result[path] = entry.object_hash
    return result
