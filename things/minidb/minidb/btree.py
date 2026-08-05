"""A textbook B-tree (CLRS-style, parameterized by minimum degree `t`),
used as an optional secondary index. Entries are (value, row_id) pairs
rather than bare values, so duplicate column values are handled for
free -- each occurrence is its own tree entry, uniquely identified by
its row position, with no special-casing needed anywhere else.

Only insert and range search are implemented -- no deletion. minidb's
executor never deletes from a B-tree directly: UPDATE/DELETE on an
indexed table just rebuilds the affected index from scratch afterward
(see executor.py's _rebuild_indexes), which is simple and always
correct at the cost of being O(n) on every mutation rather than
O(log n) -- a deliberate simplicity-over-performance tradeoff, the same
kind kvstore's README is upfront about for its own range_query.
"""
from __future__ import annotations

import bisect
from typing import List, Optional, Tuple

Entry = Tuple[object, int]  # (value, row_id)


class _Node:
    __slots__ = ("leaf", "entries", "children")

    def __init__(self, leaf: bool):
        self.leaf = leaf
        self.entries: List[Entry] = []
        self.children: List["_Node"] = []


class BTree:
    def __init__(self, min_degree: int = 32):
        if min_degree < 2:
            raise ValueError("min_degree must be at least 2")
        self.t = min_degree
        self.root = _Node(leaf=True)
        self.size = 0

    def __len__(self) -> int:
        return self.size

    def insert(self, value: object, row_id: int) -> None:
        entry = (value, row_id)
        root = self.root
        if len(root.entries) == 2 * self.t - 1:
            new_root = _Node(leaf=False)
            new_root.children.append(root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, entry)
        self.size += 1

    def _split_child(self, parent: "_Node", index: int) -> None:
        t = self.t
        child = parent.children[index]
        new_node = _Node(leaf=child.leaf)

        median_entry = child.entries[t - 1]
        new_node.entries = child.entries[t:]
        child.entries = child.entries[: t - 1]

        if not child.leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]

        parent.children.insert(index + 1, new_node)
        parent.entries.insert(index, median_entry)

    def _insert_non_full(self, node: "_Node", entry: Entry) -> None:
        if node.leaf:
            bisect.insort(node.entries, entry)
            return
        i = len(node.entries) - 1
        while i >= 0 and entry < node.entries[i]:
            i -= 1
        i += 1
        if len(node.children[i].entries) == 2 * self.t - 1:
            self._split_child(node, i)
            if entry > node.entries[i]:
                i += 1
        self._insert_non_full(node.children[i], entry)

    def range_search(self, low: Optional[object] = None, high: Optional[object] = None) -> List[Entry]:
        """All (value, row_id) entries with low <= value <= high
        (either bound may be None for an open range), in ascending
        order of value."""
        result: List[Entry] = []
        self._range_search(self.root, low, high, result)
        return result

    def _range_search(self, node: "_Node", low, high, result: List[Entry]) -> None:
        n = len(node.entries)
        i = 0
        while i < n:
            value = node.entries[i][0]
            # Safe to skip descending into children[i] when entries[i] is
            # already below `low`: every value in children[i] is smaller
            # than entries[i], so all of them would be too.
            if not node.leaf and (low is None or value >= low):
                self._range_search(node.children[i], low, high, result)
            if (low is None or value >= low) and (high is None or value <= high):
                result.append(node.entries[i])
            if high is not None and value > high:
                return  # this key and everything after it is out of range
            i += 1
        if not node.leaf:
            self._range_search(node.children[n], low, high, result)

    def search_equal(self, value: object) -> List[int]:
        return [row_id for v, row_id in self.range_search(value, value)]

    def in_order(self) -> List[Entry]:
        """Every entry, in ascending order -- used by tests to check the
        tree's internal invariants directly."""
        return self.range_search(None, None)
