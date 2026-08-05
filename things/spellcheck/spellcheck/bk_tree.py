"""A BK-tree (Burkhard-Keller tree): a metric tree that exploits the
triangle inequality to prune fuzzy search, instead of scanning the
whole dictionary for every query.

Each node stores a word; its children are keyed by their edit distance
*from the parent*. To insert a new word, walk down from the root always
following the child keyed by the new word's distance from the current
node, creating that child if it doesn't exist yet.

To query for all words within max_dist of a target: at each node with
word w, compute d = distance(target, w). If d <= max_dist, w is a hit.
Then -- the actual pruning power of the structure -- only descend into
children keyed by some distance k where |k - d| <= max_dist, because
the triangle inequality guarantees any word x in that child's subtree
satisfies |distance(x, w) - distance(target, w)| <= distance(x, target),
so distance(target, x) >= |k - d| for every x reachable that way, and
therefore can only be within max_dist if |k - d| itself is.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

DistanceFn = Callable[[str, str], int]


class _Node:
    __slots__ = ("word", "children")

    def __init__(self, word: str):
        self.word = word
        self.children: Dict[int, "_Node"] = {}


class BKTree:
    def __init__(self, distance_fn: DistanceFn):
        self.distance_fn = distance_fn
        self.root: Optional[_Node] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, word: str) -> None:
        if self.root is None:
            self.root = _Node(word)
            self._size = 1
            return
        node = self.root
        while True:
            d = self.distance_fn(word, node.word)
            if d == 0:
                return  # already present, no duplicates
            child = node.children.get(d)
            if child is None:
                node.children[d] = _Node(word)
                self._size += 1
                return
            node = child

    def query(self, target: str, max_dist: int) -> List[str]:
        if self.root is None:
            return []
        results: List[str] = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            d = self.distance_fn(target, node.word)
            if d <= max_dist:
                results.append(node.word)
            for k, child in node.children.items():
                if abs(k - d) <= max_dist:
                    stack.append(child)
        return results
