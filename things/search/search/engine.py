"""The high-level API: index documents, then search."""
from __future__ import annotations

from typing import List, Tuple

from .index import InvertedIndex
from .query import all_positive_terms, matching_documents, parse_query
from .scoring import B_DEFAULT, K1_DEFAULT, bm25_score


class SearchEngine:
    def __init__(self):
        self.index = InvertedIndex()

    def add_document(self, doc_id: int, text: str) -> None:
        self.index.add_document(doc_id, text)

    def search(
        self, query_string: str, top_k: int = 10, k1: float = K1_DEFAULT, b: float = B_DEFAULT
    ) -> List[Tuple[int, float]]:
        """Returns (doc_id, score) pairs, highest score first, ties
        broken by doc_id ascending for determinism."""
        clauses = parse_query(query_string)
        matched = matching_documents(clauses, self.index)
        terms = all_positive_terms(clauses)
        scored = [(doc_id, bm25_score(terms, doc_id, self.index, k1, b)) for doc_id in matched]
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored[:top_k]
