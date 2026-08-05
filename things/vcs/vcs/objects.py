"""Content-addressable object storage: blobs, trees, and commits are all
identified by the SHA-256 hash of a small header plus their serialized
content -- the same idea real git uses (historically with SHA-1). That
addressing scheme is what makes identical content collapse to a single
stored object for free: a file committed twice, or two different files
that happen to be byte-identical, hash to the same object and are only
ever written to disk once (see test_objects.py's dedup test).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple


def hash_object(obj_type: str, content: bytes) -> str:
    header = f"{obj_type} {len(content)}\0".encode()
    return hashlib.sha256(header + content).hexdigest()


class ObjectStore:
    def __init__(self, objects_dir: Path):
        self.objects_dir = Path(objects_dir)
        self.objects_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, object_hash: str) -> Path:
        return self.objects_dir / object_hash

    def store(self, obj_type: str, content: bytes) -> str:
        object_hash = hash_object(obj_type, content)
        path = self._path(object_hash)
        if not path.exists():
            header = f"{obj_type} {len(content)}\0".encode()
            path.write_bytes(header + content)
        return object_hash

    def load(self, object_hash: str) -> Tuple[str, bytes]:
        path = self._path(object_hash)
        if not path.exists():
            raise KeyError(f"no such object: {object_hash}")
        raw = path.read_bytes()
        header_end = raw.index(b"\0")
        obj_type, _size_str = raw[:header_end].decode().split(" ", 1)
        return obj_type, raw[header_end + 1:]

    def exists(self, object_hash: str) -> bool:
        return self._path(object_hash).exists()

    def count(self) -> int:
        return sum(1 for _ in self.objects_dir.iterdir())
