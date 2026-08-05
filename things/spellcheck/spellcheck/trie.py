"""A prefix tree for exact lookup and autocomplete."""
from __future__ import annotations

from typing import Dict, List, Optional


class _Node:
    __slots__ = ("children", "is_word")

    def __init__(self):
        self.children: Dict[str, "_Node"] = {}
        self.is_word = False


class Trie:
    def __init__(self):
        self.root = _Node()
        self._size = 0

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, _Node())
        if not node.is_word:
            self._size += 1
        node.is_word = True

    def __contains__(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_word

    def __len__(self) -> int:
        return self._size

    def _walk(self, prefix: str) -> Optional[_Node]:
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def autocomplete(self, prefix: str, limit: Optional[int] = None) -> List[str]:
        start = self._walk(prefix)
        if start is None:
            return []
        results: List[str] = []

        def dfs(node: _Node, path: List[str]) -> bool:
            if node.is_word:
                results.append(prefix + "".join(path))
                if limit is not None and len(results) >= limit:
                    return True
            for ch in sorted(node.children):
                path.append(ch)
                if dfs(node.children[ch], path):
                    return True
                path.pop()
            return False

        dfs(start, [])
        return results
