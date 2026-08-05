"""Combines a Trie (exact membership + prefix autocomplete) and a
BK-tree (fuzzy "did you mean" suggestions) into one spell-checker over a
fixed dictionary."""
from __future__ import annotations

from typing import Iterable, List, Tuple

from .bk_tree import BKTree
from .edit_distance import levenshtein
from .trie import Trie


class SpellChecker:
    def __init__(self, dictionary_words: Iterable[str]):
        words = sorted(set(dictionary_words))
        self.trie = Trie()
        self.bk_tree = BKTree(levenshtein)
        for w in words:
            self.trie.insert(w)
            self.bk_tree.insert(w)

    def is_correct(self, word: str) -> bool:
        return word in self.trie

    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        return self.trie.autocomplete(prefix, limit=limit)

    def suggest(self, word: str, max_dist: int = 2) -> List[Tuple[str, int]]:
        """Fuzzy suggestions within max_dist, closest first."""
        candidates = self.bk_tree.query(word, max_dist)
        scored = [(w, levenshtein(word, w)) for w in candidates]
        scored.sort(key=lambda pair: (pair[1], pair[0]))
        return scored
