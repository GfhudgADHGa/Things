"""A durable key-value store: every write is appended to a log and fsync'd
before the call returns, so a crash immediately after a successful put()
can never lose that write. Recovery replays the log to rebuild the
in-memory index, tolerating a torn or corrupt trailing record.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from .record import OP_DELETE, OP_PUT, encode_record, read_valid_records


class KVStore:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            open(path, "wb").close()

        self.index: Dict[str, str] = {}
        self._recover()

        self._file = open(path, "r+b")
        self._file.seek(0, os.SEEK_END)

    def _recover(self) -> None:
        with open(self.path, "rb") as f:
            records, valid_end = read_valid_records(f)

        actual_size = os.path.getsize(self.path)
        if valid_end < actual_size:
            with open(self.path, "r+b") as f:
                f.truncate(valid_end)

        for r in records:
            if r.op == OP_PUT:
                self.index[r.key.decode("utf-8")] = r.value.decode("utf-8")
            else:
                self.index.pop(r.key.decode("utf-8"), None)

    def _append(self, data: bytes) -> None:
        self._file.write(data)
        self._file.flush()
        os.fsync(self._file.fileno())

    def put(self, key: str, value: str) -> None:
        self._append(encode_record(OP_PUT, key.encode("utf-8"), value.encode("utf-8")))
        self.index[key] = value

    def get(self, key: str) -> Optional[str]:
        return self.index.get(key)

    def delete(self, key: str) -> None:
        if key not in self.index:
            return
        self._append(encode_record(OP_DELETE, key.encode("utf-8")))
        del self.index[key]

    def keys(self) -> List[str]:
        return list(self.index.keys())

    def range_query(
        self, start_key: Optional[str] = None, end_key: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """Returns (key, value) pairs with start_key <= key < end_key, sorted
        by key. Either bound may be omitted (None) for an open range.

        The index is a plain dict, not an ordered structure, so this sorts
        on every call -- O(n log n) rather than the O(log n + k) a real
        range-query engine (B-tree, LSM with sorted SSTables) would give.
        Correct and simple; genuinely not the efficient version. See the
        README's "possible expansions" note about a real index structure --
        this doesn't attempt to be that.
        """
        return sorted(
            (
                (key, value)
                for key, value in self.index.items()
                if (start_key is None or key >= start_key)
                and (end_key is None or key < end_key)
            )
        )

    def compact(self) -> None:
        """Rewrites the log to contain only the current value of each key
        (dropping overwritten values and deleted keys), shrinking it back
        down. Crash-safe: the new log is fully written and fsync'd to a
        temp file first, then swapped in with a single atomic rename --
        a crash at any point before the rename leaves the original log
        completely untouched and still valid.
        """
        tmp_path = self.path + ".compact.tmp"
        with open(tmp_path, "wb") as tmp:
            for key, value in self.index.items():
                tmp.write(encode_record(OP_PUT, key.encode("utf-8"), value.encode("utf-8")))
            tmp.flush()
            os.fsync(tmp.fileno())

        self._file.close()
        os.replace(tmp_path, self.path)
        self._file = open(self.path, "r+b")
        self._file.seek(0, os.SEEK_END)

    def __len__(self) -> int:
        return len(self.index)

    def __contains__(self, key: str) -> bool:
        return key in self.index

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "KVStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
